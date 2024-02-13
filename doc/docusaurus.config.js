// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

import { themes } from "prism-react-renderer";
const lightCodeTheme = themes.palenight;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
    title: "Gai",
    tagline: "LLM Application Development Library",
    url: "https://www.gailabs.ai",
    baseUrl: "/",
    onBrokenLinks: "throw",
    onBrokenMarkdownLinks: "warn",
    favicon: "img/favicon.ico",
    organizationName: "https://github.com/gai-labs",
    projectName: "gai-doc",

    presets: [
        [
            "classic",
            /** @type {import('@docusaurus/preset-classic').Options} */
            ({
                docs: {
                    sidebarPath: require.resolve("./sidebars.js"),
                    routeBasePath: "/docs",
                    editUrl: "https://github.com/gai-labs/gai/doc",
                },
                theme: {
                    customCss: require.resolve("./src/css/custom.css"),
                },
            }),
        ],
    ],

    themeConfig:
        /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
        ({
            colorMode: {
                disableSwitch: true,
            },
            navbar: {
                items: [
                    {
                        label: "Gai",
                        to: "/docs", // This is the path to your desired page
                        position: "left",
                        activeBaseRegex: `/`,
                    },
                ],
            },
            footer: {
                style: "dark",
                links: [
                    {
                        title: "Introduction",
                        items: [
                            {
                                label: "Introduction",
                                to: "docs/intro",
                            },
                        ],
                    },
                ],
                copyright: `Copyright © ${new Date().getFullYear()} GaiLabs Pte Ltd`,
            },
            prism: {
                theme: lightCodeTheme,
                darkTheme: darkCodeTheme,
                additionalLanguages: ["shell-session"],
            },
        }),
};

module.exports = config;
