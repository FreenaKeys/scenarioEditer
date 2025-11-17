from __future__ import annotations
import argparse
import importlib
import logging
import pkgutil
from dataclasses import dataclass
from typing import List, Protocol, runtime_checkable

# モジュール化（プラグイン化）を前提としたエントリポイントのテンプレート
# 使い方（プラグイン作成規約）
#  - プラグインは package (例: "plugins") 配下にモジュールとして配置する
#  - 各モジュールは必ず `get_plugin()` を実装して、Plugin インスタンスを返すこと
#  - Plugin は少なくとも `name: str` と `run(config: Config) -> None` を持つこと


logger = logging.getLogger("scenarioEditer")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@dataclass
class Config:
    """アプリケーション設定。必要に応じて拡張する"""
    debug: bool = False
    data_dir: str = "data"


@runtime_checkable
class Plugin(Protocol):
    """プラグインが満たすべき最小インターフェイス"""
    name: str

    def run(self, config: Config) -> None:
        ...


def discover_plugins(package: str) -> List[Plugin]:
    """
    指定 package 配下のモジュールからプラグインを発見してインスタンスを返す。
    各モジュールは `get_plugin()` を実装している必要がある。
    """
    plugins: List[Plugin] = []
    logger.info("Discovering plugins in package: %s", package)

    try:
        pkg = importlib.import_module(package)
    except ModuleNotFoundError:
        logger.warning("Package '%s' not found. No plugins loaded.", package)
        return plugins

    if not hasattr(pkg, "__path__"):
        logger.warning("Package '%s' has no __path__; cannot iterate submodules.", package)
        return plugins

    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__, package + "."):
        if ispkg:
            continue
        try:
            mod = importlib.import_module(name)
            # モジュールは get_plugin() を提供することを期待する
            if hasattr(mod, "get_plugin"):
                plugin = mod.get_plugin()
                # runtime_checkable Protocol に基づいて簡易チェック
                if isinstance(plugin, Plugin):
                    plugins.append(plugin)
                    logger.info("Loaded plugin: %s", getattr(plugin, "name", name))
                else:
                    logger.warning("Module %s: get_plugin() returned incompatible object", name)
            else:
                logger.debug("Module %s has no get_plugin(), skipping", name)
        except Exception as e:
            logger.exception("Failed to load plugin module %s: %s", name, e)

    return plugins


def run_all(plugins: List[Plugin], config: Config) -> None:
    """全てのプラグインを順に実行する"""
    for p in plugins:
        logger.info("Running plugin: %s", p.name)
        try:
            p.run(config)
        except Exception:
            logger.exception("Plugin %s raised an exception", p.name)


def create_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scenarioEditer")
    p.add_argument("--plugins", default="plugins", help="プラグインを置くパッケージ名（デフォルト: plugins）")
    p.add_argument("--data-dir", default="data", help="データディレクトリ")
    p.add_argument("--debug", action="store_true", help="デバッグモード")
    return p


def main(argv=None) -> int:
    parser = create_argparser()
    args = parser.parse_args(argv)
    cfg = Config(debug=args.debug, data_dir=args.data_dir)
    if cfg.debug:
        logger.setLevel(logging.DEBUG)
    logger.debug("Config: %s", cfg)

    plugins = discover_plugins(args.plugins)
    if not plugins:
        logger.info("No plugins found. Attempting GUI fallback (gui.app.main)...")
        try:
            gui_mod = importlib.import_module("gui.app")
            if hasattr(gui_mod, "main"):
                logger.info("Launching GUI fallback.")
                gui_mod.main()
                return 0
            else:
                logger.warning("gui.app found but has no main(); exiting.")
                return 0
        except ModuleNotFoundError:
            logger.info("No gui package found. Exiting.")
            return 0
        except Exception:
            logger.exception("Failed to launch GUI fallback")
            return 1

    run_all(plugins, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())