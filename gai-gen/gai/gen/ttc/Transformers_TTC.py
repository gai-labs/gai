from gai.common.utils import get_config_path
from gai.common import logging, generators_utils
logger = logging.getLogger(__name__)
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import os
import gc
from gai.gen.ttt.OutputBuilder import OutputBuilder

class Transformers_TTC:

    def __init__(self,gai_config):
        self.gai_config = gai_config
        self.generator_name="deepseek-transformers"
        self.model_path = os.path.join(get_config_path(),gai_config['model_path'])
        self.model = None
        self.tokenizer = None
        self.generator = None        

    def load(self):
        logger.info(f"TTC: Loading model from {self.gai_config['model_path']}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        n_gpus = torch.cuda.device_count()
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        max_memory = f'{40960}MB'
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path,
            quantization_config=bnb_config,
            device_map="auto",
            max_memory={i: max_memory for i in range(n_gpus )},)
        return self

    def unload(self):
        logger.info(f"TTC: Unloading model...")        
        try:
            del self.model
            del self.tokenizer
            del self.generator
        except:
            pass
        self.model = None
        self.tokenizer = None
        self.generator = None
        gc.collect()
        torch.cuda.empty_cache()        
        return self

    def token_count(self,text):
        return len(self.tokenizer.tokenize(text))

    def _generating(self,prompt,**model_params):
        logger.debug(f"transformers_engine.generate: prompt={prompt}")
        input_ids = self.tokenizer(prompt, return_tensors="pt",add_special_tokens=True).to(self.model.device)
        generated = self.model.generate(input_ids,**model_params)
        response = self.tokenizer.decode(generated[0], skip_special_tokens=True)
        text = response[len(prompt):]
        output = OutputBuilder.BuildContent(
                generator=self.gai_config["model_name"], 
                finish_reason='stop',
                content=text, 
                prompt_tokens=len(prompt), 
                new_tokens=len(text)
                )
        return output

    def create(self,messages,**model_params):
        if not self.tokenizer:
            self.load()
        stream = model_params.pop("stream", False)
        if not stream:
            response = self._generating(
                prompt=messages,
                **model_params
            )
            return response



