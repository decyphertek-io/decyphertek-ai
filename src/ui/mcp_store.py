import flet as ft
import json
import threading
import urllib.request
import subprocess
import sys
import os
from pathlib import Path


class MCPStoreView:
    """Minimal MCP Store tab.

    - Uses StoreManager for ALL installation/management logic
    - Loads instantly from cache
    - Shows install button or enable/disable toggle
    """

    def __init__(self, page: ft.Page, store_manager, skills_url: str | None = None):
        self.page = page
        self.store_manager = store_manager
        self.skills_url = (
            skills_url
            or "https://raw.githubusercontent.com/decyphertek-io/mcp-store/main/skills.json"
        )
        self.user_home = Path.home() / ".decyphertek-ai"
        self.user_store = self.user_home / "store"
        self.mcp_store_root = self.user_store / "mcp"
        self.cache_path = self.mcp_store_root / "cache.json"
        self.registry: dict = {}
        self._init_started = False
        self._installing: dict[str, bool] = {}
        self._list_column: ft.Column | None = None

    def build(self) -> ft.Control:
        # Background fetch once; do not block render
        if not self._init_started:
            self._init_started = True

            def _bg_fetch():
                try:
                    self.registry = self._fetch_skills()
                    self._write_registry_cache(self.registry)
                except Exception as e:
                    print(f"[MCPStore] Fetch error: {e}")
                self._refresh()

            threading.Thread(target=_bg_fetch, daemon=True).start()

        # Load cached registry for instant render
        if not self.registry:
            cached_reg = self._read_registry_cache()
            if isinstance(cached_reg, dict):
                self.registry = cached_reg

        servers = self._servers_for_ui()

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.CLOUD, size=28),
                    ft.Text("MCP Servers", size=22, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.icons.ADD, tooltip="Add Store", on_click=lambda e: self._add_custom_store()),
                    ft.IconButton(icon=ft.icons.REFRESH, tooltip="Refresh", on_click=lambda e: self._refresh()),
                ]
            ),
            padding=15,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        self._list_column = ft.Column(
            [self._server_row(s) for s in servers],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        return ft.Container(
            content=ft.Column(
                [
                    header,
                    ft.Container(height=10),
                    self._list_column if servers else ft.Text("No servers cached yet.", size=12, color=ft.colors.GREY_600),
                ],
                expand=True,
            ),
            expand=True,
        )

    def _refresh(self):
        try:
            # Rebuild rows from latest state
            if self._list_column is not None:
                servers = self._servers_for_ui()
                self._list_column.controls = [self._server_row(s) for s in servers]
                if getattr(self._list_column, "page", None) is not None:
                    self._list_column.update()
            self.page.update()
        except Exception:
            pass

    # ------------
    # UI builders
    # ------------
    def _server_row(self, s: dict) -> ft.Control:
        sid = s["id"]
        installed = s.get("installed", False)
        enabled = s.get("enabled", False)

        if self._installing.get(sid):
            action = ft.ProgressRing(width=20, height=20)
        elif not installed:
            action = ft.IconButton(icon=ft.icons.DOWNLOAD, tooltip="Install", on_click=lambda e, sid=sid: self._install_server(sid))
        else:
            action = ft.Switch(value=enabled, on_change=lambda e, sid=sid: self._set_enabled(sid, e.control.value), tooltip="Enable/Disable")

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.CLOUD, size=24, color=ft.colors.BLUE),
                    ft.Column([
                        ft.Text(self._name_for(sid), size=14, weight=ft.FontWeight.W_600),
                        ft.Text(f"{sid}", size=11, color=ft.colors.GREY_600),
                    ], spacing=2, expand=True),
                    action,
                ]
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=8,
            padding=10,
        )

    # -----------------
    # Actions & helpers
    # -----------------
    def _add_custom_store(self):
        url_field = ft.TextField(
            label="Raw skills.json URL",
            hint_text="https://raw.githubusercontent.com/your-org/mcp-store/main/skills.json",
            value="",
            expand=True,
        )

        def apply_url(_):
            url = url_field.value.strip()
            if url:
                self.skills_url = url
                # Refetch in background
                def _bg():
                    try:
                        self.registry = self._fetch_skills()
                    except Exception as e:
                        print(f"[MCPStore] Custom fetch error: {e}")
                    self._refresh()
                threading.Thread(target=_bg, daemon=True).start()
            self.page.close(dialog)
            self._refresh()

        dialog = ft.AlertDialog(
            title=ft.Text("Add custom MCP Store"),
            content=url_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Apply", icon=ft.icons.CHECK, on_click=apply_url),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _install_server(self, sid: str):
        """Install MCP server using StoreManager"""
        if self._installing.get(sid):
            return
        self._installing[sid] = True
        self._refresh()

        def _bg_install():
            try:
                # Let StoreManager handle EVERYTHING: download, Poetry venv, enable
                result = self.store_manager.install_mcp_server(sid)
                if result.get("success"):
                    print(f"[MCPStore] ✅ {sid} installed successfully")
                else:
                    print(f"[MCPStore] ❌ {sid} install failed: {result.get('error')}")
            except Exception as e:
                print(f"[MCPStore] Install error for {sid}: {e}")
            finally:
                self._installing[sid] = False
                self._refresh()

        threading.Thread(target=_bg_install, daemon=True).start()

    def _set_enabled(self, sid: str, value: bool, write_only: bool = False):
        """Enable/disable MCP server using StoreManager"""
        self.store_manager.set_mcp_enabled(sid, bool(value))
        if not write_only:
            self._refresh()

    def _servers_for_ui(self) -> list[dict]:
        servers = []
        cache = self._read_cache()
        if self.registry.get("servers"):
            for sid, info in self.registry["servers"].items():
                servers.append({
                    "id": sid,
                    "installed": bool(cache.get(sid, {}).get("installed", False)),
                    "enabled": bool(cache.get(sid, {}).get("enabled", False)),
                    "name": info.get("name", self._name_for(sid)),
                    "description": info.get("description", f"{sid}"),
                })
        else:
            for sid in ["web-search", "nextcloud", "google-drive"]:
                servers.append({
                    "id": sid,
                    "installed": bool(cache.get(sid, {}).get("installed", False)),
                    "enabled": bool(cache.get(sid, {}).get("enabled", False)),
                    "name": self._name_for(sid),
                    "description": sid,
                })
        return servers

    def _fetch_skills(self) -> dict:
        with urllib.request.urlopen(self.skills_url, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _read_registry_cache(self) -> dict:
        try:
            self.local_root.mkdir(parents=True, exist_ok=True)
            if self.registry_cache_path.exists():
                return json.loads(self.registry_cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _write_registry_cache(self, data: dict) -> None:
        try:
            self.local_root.mkdir(parents=True, exist_ok=True)
            self.registry_cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _read_cache(self) -> dict:
        try:
            self.local_root.mkdir(parents=True, exist_ok=True)
            if self.cache_path.exists():
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _write_cache(self, data: dict) -> None:
        try:
            self.local_root.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _write_cache_entry(self, sid: str, installed: bool | None = None, enabled: bool | None = None) -> None:
        data = self._read_cache()
        entry = data.get(sid, {})
        if installed is not None:
            entry["installed"] = installed
        if enabled is not None:
            entry["enabled"] = enabled
        data[sid] = entry
        self._write_cache(data)

    def _contents_api_url(self, repo_url: str, folder_path: str, ref: str = "main") -> str:
        try:
            parts = repo_url.rstrip("/").split("/")
            owner, repo = parts[-2], parts[-1]
        except Exception:
            owner, repo = "decyphertek-io", "mcp-store"
        folder = folder_path.strip("/")
        return f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}?ref={ref}"


    def _name_for(self, sid: str):
        return sid.replace("-", " ").title()


