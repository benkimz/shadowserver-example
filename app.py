#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import asyncio

from shadowserver import ShadowServer

class ProxyServerApp(ShadowServer):
    def __init__(self, settings_file, *args, **kwargs) -> None:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
            self.remote_server_uri = settings.get("remote_server").get("uri")
            self.application_id = settings.get("application_id")
            self.proxy_server = settings.get("proxy_server")
            self.applications_root = settings.get("applications_root")
            self.entry_point = settings.get("entry_point")

        if self.remote_server_uri is not None:
            super().__init__(
                target_base_url=self.remote_server_uri, 
                route=self.entry_point or "/", *args, **kwargs)
        else: raise ValueError("Remote server URI is not defined in settings file.")

    def is_static_resource(self, path_info):
        return bool(re.search(r'\.[a-zA-Z0-9]+$', path_info))

    def construct_target_url(self, request, route=""):
        path_info = route or request.match_info['path_info']

        resolved_from_root = path_info.startswith("_blazor") or self.is_static_resource(path_info=path_info)

        # Route requests with the project prefix if accessing an app route, not static resources.
        if not resolved_from_root:
            target_url = f"{self.target_base_url}{self.applications_root}/{self.application_id}/{path_info}".rstrip("/")
        else:
            target_url = f"{self.target_base_url}/{path_info}".rstrip("/")        

        if request.query_string:
            target_url += f"?{request.query_string}"

        return target_url  

    def run(self, host=None, port=None):
        if host is not None and port is not None:
            self.proxy_server.update({"host": host, "port": port})
        host, port = self.proxy_server.get("host"), self.proxy_server.get("port")
        if host is None or port is None: 
            raise ValueError("Proxy server host or port is not defined in settings file.")
        if self.application_id is None: 
            raise ValueError("Application ID is not defined in settings file.")
        if self.remote_server_uri is not None:
            print(f"<< Remote server: {self.remote_server_uri} >>")

        asyncio.run(self.start_server(host=host, port=port))


app = ProxyServerApp(settings_file="settings.json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)