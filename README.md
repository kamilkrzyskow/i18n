# MkDocs static i18n plugin

![mkdocs-static-i18n pypi version](https://img.shields.io/pypi/v/mkdocs-static-i18n.svg)

*An MkDocs plugin that helps you support multiple language versions of your site / documentation.*

*Like what you :eyes:? Using this plugin? Give it a :star:!*

The `mkdocs-static-i18n` plugin allows you to support multiple languages of your documentation by adding static translation files to your existing documentation pages.

Multi language support is just **one `.<language>.md` file away**!

Even better, `mkdocs-static-i18n` also allows you to build and serve [**localized versions of any file extension**](#referencing-localized-content-in-your-markdown-pages) to display localized images, medias and assets.

Localized images/medias/assets are just **one `.<language>.<extension>` file away**!

If you want to see how it looks, [check out the demo documentation here](https://ultrabug.github.io/mkdocs-static-i18n/).

## Language detection logic

This plugin is made to be as simple as possible and will generate a default version of your website + one version per configured language on the `<language>/` path.

Your translations can be detected using a **suffix based docs structure** (default) or a **folder based docs structure**. This is controlled by the [docs_structure](#docs_structure) option.

Since demonstrations are better than words, [check out the demo documentation here](https://ultrabug.github.io/mkdocs-static-i18n/) which showcases the logic.

### Suffix based docs structure

The **default** behavior is to use a **suffix based docs structure** to handle your translations:

- the `default` version will use any `.md` documentation file first and fallback to any `.<default_language>.md` file found
- the `/<language>` language versions will use any `.<language>.md` documentation file first and fallback to any `.<default_language>.md` file before fallbacking to any default `.md` file found

### Folder based docs structure

The optional behavior is to use a **folder based structure** to handle your translations:

- each of your configured language should have a folder with their name at the root of `docs_dir`, which of course includes the default language of your choice
- then you just structurate your `.md` documentation files in their respective folder structure
- any folder relative to `docs_dir` which is not a language folder will be copied as-is and their files will serve as language agnostic (think of non localized images)

See a [using a folder per language structure](#using-a-folder-per-language-structure) section for more details.

## Installation

Just `pip install mkdocs-static-i18n`!

## Configuration

Here is the list of all the options that the plugin supports.

### default_language

- mandatory: `yes`

A 2-letter [ISO-639-1](https://en.wikipedia.org/wiki/ISO_639-1) language code (`en`) or [5-letter language code with added territory/region/country](https://www.mkdocs.org/user-guide/localizing-your-theme/#supported-locales) (`en_US`).

```yaml
default_language: en
```

### default_language_only

- default: `false`

This **boolean** (true/false) option is used to [speed up the build process while developing your documentation](#building-only-the-default-language-for-faster-development).

```yaml
default_language_only: false
```

### docs_structure

- default: `suffix`

This **(fixed) string** (can be either 'suffix' or 'folder') option is used to select which [language detection logic](#language-detection-logic) should be used to build the localized versions of your documentation.

```yaml
docs_structure: folder
```

### languages

- mandatory: `yes`

A mapping of **2-letter or 5-letter language code** (like `default_language`) with **either** the display name of the language **or** some optional keys used to control the build process of each language.

Allowed options per language:

- `name` (mandatory): the name that should be displayed in the [mkdocs-material language switcher](#using-mkdocs-material-site-language-selector)
- `link` (default: `./<language>`): the link path to be used in the [mkdocs-material language switcher](#using-mkdocs-material-site-language-selector)
- `fixed_link` (default: `None`): if specified, when switching to this language, you will be redirected to this link
- `build` (default: `true`): a boolean used to control the build of a `/<language>` path for the given language
- `site_name` (default: `mkdocs.yml site_name`): the [`site_name` translation for the given language](#translating-site-name)

Feature rich `languages` options usage:

```yaml
plugins:
  - i18n:
      default_language: en
      languages:
        en:
          name: English
          build: true
        fr:
          name: Français
          build: true
```

Short (legacy) `languages` options usage:

```yaml
plugins:
  - i18n:
      default_language: en
      languages:
        en: English
        fr: Français
```

### material_alternate

- default: `true`

If you're using the mkdocs-material theme, this **boolean** (true/false) option will let you choose if you want the mkdocs-static-i18n plugin to [configure the language switcher for you.](#using-mkdocs-material-site-language-selector).

```yaml
material_alternate: true
```

### nav_translations

- default: `empty`

This option is a nested mapping of **language**: **default title**: **translated title** that allows you to [translate the navigation sections of your website](#translating-navigation).

```yaml
nav_translations:
  fr:
    Topic1: Sujet1
    Topic2: Sujet2
```

### search_reconfigure

- default: `true`

This is a **boolean** (true/false) option that lets you activate or not [the automatic reconfiguration](#compatibility-with-the-search-plugin) of the `plugins.search.lang` option based on your configured languages.

## Example configuration and output

```yaml
plugins:
  - i18n:
      default_language: en
      languages:
        en:
          name: English
          build: true
        fr:
          name: Français
          build: true
```

Using the configuration above on the following `docs/` structure will build the following `site/` (leaving out static files for readability):

```
docs
├── image.en.png
├── image.fr.png
├── index.fr.md
├── index.md
├── topic1
│   ├── index.en.md
│   └── index.fr.md
└── topic2
    ├── index.en.md
    └── index.md
```

```
site
├── en
│   ├── image.png
│   ├── index.html
│   ├── topic1
│   │   └── index.html
│   └── topic2
│       └── index.html
├── fr
│   ├── image.png
│   ├── index.html
│   ├── topic1
│   │   └── index.html
│   └── topic2
│       └── index.html
├── image.png
├── index.html
├── topic1
│   └── index.html
└── topic2
    └── index.html
```

### Alternate aware sitemap.xml

The `mkdocs-static-i18n` plugin since version 0.32 provides a template that will generate automatically an alternate aware `sitemap.xml` so that your localized content is made available to search engines!

Localization aware sitemap.xml:

```xml
    <url>
         <loc>https://ultrabug.github.io/mkdocs-static-i18n/</loc>
         <lastmod>2022-01-31</lastmod>
         <changefreq>daily</changefreq>
         <xhtml:link rel="alternate" hreflang="en" href="https://ultrabug.github.io/mkdocs-static-i18n/en/"/>
         <xhtml:link rel="alternate" hreflang="fr" href="https://ultrabug.github.io/mkdocs-static-i18n/fr/"/>
    </url>
```

### Not building a dedicated version for the default language

If you do not wish to build a dedicated `<language>/` path for the `default_language` version of your documentation, just **set its `build` option to `false`**.

The following configuration:

```yaml
plugins:
  - i18n:
      default_language: en
      languages:
        fr:
          name: Français
          build: true
        en:
          name: English
          build: false
```

Applied on the following structure:

```
docs
├── image.en.png
├── image.fr.png
├── index.fr.md
├── index.md
├── topic1
│   ├── index.en.md
│   └── index.fr.md
└── topic2
    ├── index.en.md
    └── index.md
```

Will build:

```
site
├── fr
│   ├── image.png
│   ├── index.html
│   ├── topic1
│   │   └── index.html
│   └── topic2
│       └── index.html
├── image.png
├── index.html
├── topic1
│   └── index.html
└── topic2
    └── index.html
```

## Building only the default language for faster development

When working on your project, building a version for each supported language
can be slow depending on the size of your documentation.

The `default_language_only` option allows you to only build the selected
`default_language` of your documentation for faster development.

Coupled with [MkDocs >= 1.2 support for environment variables](https://www.mkdocs.org/about/release-notes/#support-added-for-environment-variables-in-the-configuration-file-1954),
this option can easily be passed dynamically [within your `mkdocs.yml` file like this](https://github.com/ultrabug/mkdocs-static-i18n/blob/main/mkdocs.yml)!

You can [read more about the rationale behind this feature here](https://github.com/ultrabug/mkdocs-static-i18n/issues/32#issuecomment-860563081).

### Referencing localized content in your markdown pages

Focus on translating your content, not on updating all the links and references
to your assets!

Let `mkdocs-static-i18n` do the heavy lifting of dynamically localizing your
assets and just reference everything without their localized extension.

Since the generated `site` files have their localization extension removed
during the build process, you can reference them in your markdown source
without it (this includes links to `.md` files)!

This simple docs structure:

```
docs
├── image.en.png
├── image.fr.png
├── index.fr.md
├── index.md
```

Will generate this site tree:

```
site
├── fr
│   ├── image.png
│   ├── index.html
├── image.png
├── index.html
```

Which means that the `image.png` and its `fr/image.png` localized counterpart
can be referenced the same way as `![my image](image.png)` on both `index.md`
and `index.fr.md`!

## Translating site name

Using the `site_name` option for a given language, you can translate the site
name that will be used to render the localized pages for the language version
of your website.

```yaml
site_name: Default site title

plugins:
  - i18n:
      default_language: en
      languages:
        en:
          name: English
          site_name: Site title in English for pages with path /en/
        fr:
          name: Français
          site_name: Titre du site en Français pour les pages en /fr/
```

## Translating navigation

Using the `nav_translations` configuration option, you can translate all your
navigation titles easily.

**Translations are applied to all titles** so you only need to provide a given
translation once and it will be used to translate all the sections, links and
pages which share the same title.

This example will translate **any** navigation item title from **Topic1** to
**Sujet1** on the French version of the documentation:

```yaml
plugins:
  - i18n:
      default_language: en
      languages:
        en:
          name: English
        fr:
          name: Français
      nav_translations:
        fr:
          Topic1: Sujet1
          Topic2: Sujet2
```

## Localized content can diverge from the default version

Since version 0.20 of the plugin, localized content can diverge from the
default language version. This means that you can have pages that are specific
to some languages without any problem.

See #59 if you need more information about this.

## Compatibility with the search plugin

If you enabled the `search` plugin embedded with MkDocs, this plugin will
automatically populate its `lang` option with the the configured `languages`
as long as they are supported by [lunr](https://pypi.org/project/lunr/).

:warning: **Search results will include all the pages from all the localized
contents!**

This means that your search results can't be contextual to the language
you are currently browsing.

The `mkdocs-static-i18n` plugin will try to be smart and [deduplicate the pages](https://github.com/ultrabug/mkdocs-static-i18n/issues/129) from the `default_language` so that search results are not polluted by redundant content.

This is because the MkDocs `search` plugin is hardcoded in the themes
javascript sources so there can only be one search index for the whole
build.

This feature can be disabled using the `search_reconfigure` option.

## Compatibility with other plugins

This plugin is compatible with the following mkdocs plugins:

- [MkDocs Material](https://github.com/squidfunk/mkdocs-material): the `search` plugin text will be switched automatically to the right language depending on the version you're browsing and the `language selector` will automatically be setup for you (requires mkdocs-material>=7.1.0)
- [MkDocs Awesome Pages Plugin](https://github.com/lukasgeiter/mkdocs-awesome-pages-plugin): the page ordering is preserved on the language specific versions of your site
- [MkDocs with PDF Plugin](https://github.com/orzih/mkdocs-with-pdf): you get a PDF of every localized version of your site
- [MkDocs minify Plugin](https://github.com/byrnereese/mkdocs-minify-plugin): to minify your JS, CSS and HTML localized files

## Adding a language selector on your documentation header

### Using mkdocs-material site language selector

Starting version 7.1.0, [mkdocs-material supports a site language selector](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/#site-language-selector) configuration.

The `mkdocs-static-i18n` plugin will detect if you're using `mkdocs-material` and, if its version is at least `7.1.0`, **will enable and configure the site language selector automatically for you** unless you specified your own `extra.alternate` configuration!

Even better, `mkdocs-static-i18n` will also make it so that changing between languages keeps you on the same page instead of getting you back to the language specific home page (not compatible with theme.features = navigation.instant, [see #62](https://github.com/ultrabug/mkdocs-static-i18n/issues/62))!

If you wish to disable that feature, simply set the `material_alternate` option to `false`:

```yaml
plugins:
  - i18n:
      default_language: en
      languages:
        en:
          name: English
        fr:
          name: Français
      material_alternate: false
```

### Writing a custom language switcher

Let's take `mkdocs-material` as an example and say we would like to add two buttons to allow our visitors to switch to their preferred language.

The following explanation was showcased in the demo website up to 0.7 so you can find the files here:

- [mkdocs.yml](https://github.com/ultrabug/mkdocs-static-i18n/tree/0.7/mkdocs.yml)
- [theme_overrides](https://github.com/ultrabug/mkdocs-static-i18n/tree/0.7/theme_overrides/partials)

We need to add a `custom_dir` to our `theme` configuration:

```yaml
theme:
  name: material
  custom_dir: theme_overrides
```

Then override the `header.html` to insert something like:

```
    {% if "i18n" in config.plugins %}
      <div style="margin-left: 10px; margin-right: 10px;">
          {% include "partials/i18n_languages.html" %}
      </div>
    {% endif %}
```

And add a `i18n_languages.html` that could look like this:

```
{% for lang, display in config.plugins.i18n.config.languages.items() -%}
    <div style="display: inline-block; margin-right:5px;"><a href="/{{ lang }}/">{{ display }}</a></div>
{% endfor %}
```

The resulting files should be placed like this:

```
theme_overrides
└── partials
    ├── header.html
    └── i18n_languages.html
```

## Using i18n context variables in your pages

The plugin exports some useful i18n variables that you can access through the page context:

- `i18n_config`: the i18n plugin configuration
- `i18n_page_locale`: the current rendering locale of the page
- `i18n_page_file_locale`: the locale suffix of the source file used to render the page

Those context [variables can be accessed using Jinja2 notation](https://jinja.palletsprojects.com/en/latest/templates/#variables), like `{{ i18n_page_locale }}` in your theme overrides.

## Using a folder per language structure

:warning: The **folder structure feature is not as mature as the suffix one** and should be used only for large and complex translation layouts. The folder structure is also very strict about your `docs_dir` layout so make sure you respect it properly.

The `mkdocs-static-i18n` plugin can be configured to work with a **language per folder based structure** where you create a folder per language your want to support translations for.

For example, the given folder structure:

```
docs_folder_structure
├── assets
│   └── image_non_localized.png
├── en
│   ├── image.png
│   ├── index.md
│   ├── topic1
│   │   └── named_file.md
│   └── topic2
│       └── README.md
└── fr
    ├── image.png
    ├── index.md
    ├── topic1
    │   └── named_file.md
    └── topic2
        └── README.md
```

With the following `mkdocs.yml` configuration:

```yaml
plugins:
  - i18n:
      default_language: en
      docs_structure: folder
      languages:
        en:
          name: English
        fr:
          name: Français
```

Will build:

```
site
├── assets
│   └── image_non_localized.png
├── en
│   ├── image.png
│   ├── index.html
│   ├── topic1
│   │   └── index.html
│   └── topic2
│       └── index.html
├── fr
│   ├── image.png
│   ├── index.html
│   ├── topic1
│   │   └── index.html
│   └── topic2
│       └── index.html
├── image.png
├── index.html
├── topic1
│   └── index.html
└── topic2
    └── index.html
```

## See it in action

- [On this repository demo website](https://ultrabug.github.io/mkdocs-static-i18n/)
- [On my own website: ultrabug.fr](https://ultrabug.fr)

## Contributions welcome

Feel free to ask questions, enhancements and to contribute to this project!
