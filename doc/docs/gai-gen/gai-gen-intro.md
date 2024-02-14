---
id: gai-gen-intro
title: Gai/Gen Introduction
sidebar_position: 1
---

## Gai/Gen: Local LLM Application Development Library

Main focus of this library is to provide interaction local LLMs. Not all interactions are solely dealing with models. For example, in retrieval-augmented generation, the underlying technology is a combination of 2 language models and a vector database but is abstracted into a single category so that it can be treated and be used like any other models. The library centers around a singleton wrapper designed to interface with only one model at a time. Typically, you will then run this as an API service. We shall call this single model services as **Gai Instances**. For more complex scenarios, such as developing multi-modal application or multi-agent chatbot, you may require a cluster of Gai Instances. You can simply deploy your own cluster through a cloud provider or use Gai-AIO, a service from GaiLabs for hosting and managing cluster of Gai Instances.
