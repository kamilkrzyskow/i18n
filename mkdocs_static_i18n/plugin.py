import logging
from pathlib import Path, PurePath
from typing import Optional

from jinja2.ext import loopcontrols
from mkdocs import plugins
from mkdocs.commands.build import DuplicateFilter, build
from mkdocs.config import load_config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from mkdocs_static_i18n import suffix
from mkdocs_static_i18n.reconfigure import ExtendedPlugin

try:
    from importlib.metadata import files as package_files
    from importlib.metadata import version

    material_version = version("mkdocs-material")
    material_languages = [
        lang.stem
        for lang in package_files("mkdocs-material")
        if "material/partials/languages" in lang.as_posix()
    ]
except Exception:
    try:
        # python 3.7 compatibility, drop on 3.7 EOL
        import pkg_resources

        material_dist = pkg_resources.get_distribution("mkdocs-material")
        material_version = material_dist.version
        material_languages = [
            lang.split(".html")[0]
            for lang in material_dist.resource_listdir("material/partials/languages")
        ]
    except Exception:
        material_languages = []
        material_version = None

log = logging.getLogger("mkdocs.plugins." + __name__)


class I18n(ExtendedPlugin):
    """
    We use 'event_priority' to make sure that we are last plugin to be executed
    because we need to make sure that we react to other plugins' behavior
    properly.

    Current plugins we heard of and require that we control their order:
        - awesome-pages: this plugin should run before us
        - with-pdf: this plugin is triggerd by us on the appropriate on_* events
    """

    @plugins.event_priority(-100)
    def on_config(self, config: MkDocsConfig):
        """
        Enrich configuration with language specific knowledge.
        """
        # first execution, setup defaults
        if self.current_language is None:
            self.current_language = self.default_language
        # reconfigure the mkdocs config
        return self.reconfigure_mkdocs_config(config)

    @plugins.event_priority(-100)
    def on_files(self, files: Files, config: MkDocsConfig):
        """
        Construct the lang specific file tree which will be used to
        generate the navigation for the default site and per language.
        """
        if self.config["docs_structure"] == "suffix":
            i18n_files = suffix.on_files(self, files, config)
        else:
            raise Exception("unimplemented")
        # reconfigure the alternates map by build language
        self.i18n_alternates = self.reconfigure_alternates(i18n_files)
        return i18n_files

    @plugins.event_priority(-100)
    def on_nav(self, nav, config, files):
        """
        Translate i18n aware navigation to honor the 'nav_translations' option.
        """

        homepage_suffix: str = "" if config.use_directory_urls else "index.html"

        # maybe move to another file and don't pass it as parameter?
        class NavHelper:
            translated_items: int = 0
            homepage: Optional[Page] = nav.homepage
            expected_homepage_urls = [
                f"{self.current_language}/{homepage_suffix}",
                f"/{self.current_language}/{homepage_suffix}",
            ]

        i18n_nav = self.reconfigure_navigation(nav, config, files, NavHelper)
        i18n_nav.homepage = NavHelper.homepage

        # report translated entries
        if NavHelper.translated_items:
            log.info(
                f"Translated {NavHelper.translated_items} navigation element"
                f"{'s' if NavHelper.translated_items > 1 else ''} to '{self.current_language}'"
            )

        # report missing homepage
        if i18n_nav.homepage is None:
            log.warning(f"Could not find a homepage for locale '{self.current_language}'")

        # manually trigger with-pdf, see #110
        with_pdf_plugin = config["plugins"].get("with-pdf")
        if with_pdf_plugin:
            with_pdf_plugin.on_nav(i18n_nav, config, files)

        return i18n_nav

    def on_env(self, env, config, files):
        # Add extension to allow the "continue" clause in the sitemap template loops.
        env.add_extension(loopcontrols)

        # find the search plugin to find out its class
        for name, plugin in config.plugins.items():
            if name in ["search", "material/search"]:
                search_plugin = plugin
                break
        else:
            search_plugin = None

        if not search_plugin or self.current_language == self.default_language:
            return None

        def change_site_dir(func):
            """Decorator to add a directory to the `site_dir` path"""

            def wrapper(*args, **kwargs):
                site_dir = kwargs.get("config", {}).get("site_dir")
                if site_dir is None:
                    return func(*args, **kwargs)
                kwargs["config"]["site_dir"] = str(PurePath(site_dir) / self.current_language)
                return func(*args, **kwargs)

            return wrapper

        # wrap the post_build event and change the site_dir path
        # it will save the search_index in the correct directory
        for i, event in enumerate(config.plugins.events["post_build"]):
            if not hasattr(event, "__self__"):
                continue
            if event.__self__.__class__ is search_plugin.__class__:
                config.plugins.events["post_build"][i] = change_site_dir(event)
                break

    @plugins.event_priority(-100)
    def on_template_context(self, context, template_name, config):
        """
        Template context only applies to Template() objects.
        We add some metadata for users and our sitemap.xml generation.
        """
        # convenience for users in case they need it (we don't)
        context["i18n_build_languages"] = self.build_languages
        context["i18n_current_language_config"] = self.current_language_config
        context["i18n_current_language"] = self.current_language
        # used by sitemap.xml template
        context["i18n_alternates"] = self.i18n_alternates
        return context

    @plugins.event_priority(-100)
    def on_post_template(
            self, output: str, *, template_name: str, config: MkDocsConfig
    ) -> Optional[str]:

        if template_name == 'sitemap.xml':
            return None

        # Pass the base path of the current language to JavaScript
        # TODO extract to a function same with `on_post_page`
        current_language = next(
            filter(lambda l: l.locale == self.current_language, self.config.languages)
        )
        i18_link = current_language.link.replace("./", "")
        return output.replace("<script", f'<script>let i18n_link = "{i18_link}";</script><script', 1)

    @plugins.event_priority(-100)
    def on_page_context(self, context, page, config, nav):
        """
        Page context only applies to Page() objects.
        We add some metadata for users as well as some neat reconfiguration features.

        Overriden templates such as the sitemap.xml are not impacted by this method!
        """
        # export some useful i18n related variables on page context, see #75
        context["i18n_config"] = self.config
        context["i18n_page_locale"] = page.file.locale
        if self.config["reconfigure_material"] is True:
            context = self.reconfigure_page_context(context, page, config, nav)
        return context

    @plugins.event_priority(-100)
    def on_post_page(self, output, page, config):
        """
        Some plugins we control ourselves need this event.
        """
        # manually trigger with-pdf, see #110
        with_pdf_plugin = config["plugins"].get("with-pdf")
        if with_pdf_plugin:
            with_pdf_plugin.on_post_page(output, page, config)

        # Pass the base path of the current language to JavaScript
        current_language = next(
            filter(lambda l: l.locale == self.current_language, self.config.languages)
        )
        i18_link = current_language.link.replace("./", "")
        return output.replace("<script", f'<script>let i18n_link = "{i18_link}";</script><script', 1)

    @plugins.event_priority(-100)
    def on_post_build(self, config):
        """
        We build every language on its own directory.
        """

        # memorize locale search entries
        # self.extend_search_entries(config)

        if self.building:
            return

        self.building = True

        # Block time logging for internal builds
        duplicate_filter: DuplicateFilter = logging.getLogger("mkdocs.commands.build").filters[0]
        duplicate_filter.msgs.add("Documentation built in %.2f seconds")

        # manually trigger with-pdf, see #110
        with_pdf_plugin = config["plugins"].get("with-pdf")
        if with_pdf_plugin:
            with_pdf_output_path = with_pdf_plugin.config["output_path"]
            with_pdf_plugin.on_post_build(config)

        # monkey patching mkdocs.utils.clean_directory to avoid
        # the site_dir to be cleaned up on each build() call
        from mkdocs import utils

        mkdocs_utils_clean_directory = utils.clean_directory
        utils.clean_directory = lambda x: x

        for locale in self.build_languages:
            if locale == self.current_language:
                continue
            self.current_language = locale

            # TODO: reconfigure config here? skip on_config?
            # create a new internal config for additional languages
            internal_config = load_config(config.config_file_path)

            # remove the initially created I18n events
            # required to avoid running 2 instances of the plugin
            for event_group in internal_config.plugins.events.values():
                for i, event in enumerate(event_group):
                    if not hasattr(event, "__self__"):
                        continue
                    if event.__self__.__class__ is self.__class__:
                        event_group.pop(i)
                        break

            # reassign the plugin, the events will be registered again
            internal_config.plugins["i18n"] = config.plugins["i18n"]

            log.info(f"Building '{locale}' documentation to directory: {internal_config.site_dir}")
            build(internal_config)

            # manually trigger with-pdf for this locale, see #110
            if with_pdf_plugin:
                with_pdf_plugin.config["output_path"] = PurePath(
                    f"{locale}/{with_pdf_output_path}"
                ).as_posix()
                with_pdf_plugin.on_post_build(internal_config)

        if config.theme.name == "material":
            # make search_index path i18n aware
            replace_pairs = [
                ('"search/search_index.json"', '`${i18n_link}search/search_index.json`')
            ]
        else:
            # 1. create a variable to hold the i18n_link inside the worker
            # 2. pass the i18n_link to the worker with the init object
            # 3. assign passed i18_link to the variable
            # 4. make search_index path i18n aware
            # 5. make additional JavaScript resources paths i18n aware
            replace_pairs = [
                (
                    "base_path = 'function' === typeof importScripts ? '.' : '/search/';",
                    "base_path = 'function' === typeof importScripts ? '.' : '/search/'; let i18n_link;",
                ),
                ('({init: true});', '({init: true, i18n_link: i18n_link});'),
                ('if (e.data.init) {', 'if (e.data.init) { i18n_link = e.data.i18n_link;'),
                ('"GET", index_path', '"GET", `../${i18n_link}search/search_index.json`'),
                (
                    ".push('lunr.stemmer.support.js');",
                    ".push(`../${i18n_link}search/lunr.stemmer.support.js`);",
                ),
                (".push('lunr.multi.js');", ".push(`../${i18n_link}search/lunr.multi.js`);"),
                (".push('tinyseg.js');", ".push(`../${i18n_link}search/tinyseg.js`);"),
                (
                    ".push(['lunr', lang[i], 'js'].join('.'));",
                    ".push([`../${i18n_link}search/lunr`, lang[i], 'js'].join('.'));",
                ),
            ]

        for old, new in replace_pairs:
            for path in Path(config.site_dir).glob("**/*.js"):
                src = path.read_text(encoding="utf-8-sig")
                out = src.replace(old, new)
                if src != out:
                    path.write_text(out, encoding="utf8")
                    log.info(f"Modified search_index JavaScript: {path}")
                    break
            else:
                log.error(
                    f"search_index JavaScript wasn't modified, theme {config.theme.name} is bad "
                    "consider downgrading the version of the theme, because it worked before ;)"
                )

        # rebuild and deduplicate the search index
        # self.reconfigure_search_index(config)

        # remove monkey patching in case some other builds are triggered
        # on the same site (tests, ci...)
        utils.clean_directory = mkdocs_utils_clean_directory

        # Unblock time logging after internal builds
        duplicate_filter.msgs.remove("Documentation built in %.2f seconds")
