// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

import { themes } from "prism-react-renderer";
const lightCodeTheme = themes.palenight;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
    title: "Gai",
    tagline: "LLM Application Development Library",
    url: "https://gai-labs.github.io",
    //baseUrl: process.env.NODE_ENV === "development" ? "/" : "/gai/",
    baseUrl: "/",
    onBrokenLinks: "throw",
    onBrokenMarkdownLinks: "warn",
    favicon: "img/favicon.ico",
    organizationName: "gai-labs",
    projectName: "gai",

    presets: [
        [
            "classic",
            /** @type {import('@docusaurus/preset-classic').Options} */
            ({
                docs: {
                    sidebarPath: require.resolve("./sidebars.js"),
                    routeBasePath: "/",
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
                        to: "/",
                        position: "left",
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
                                to: "/",
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
