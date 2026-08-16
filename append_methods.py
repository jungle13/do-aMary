with open('c:\\Users\\Home\\.gemini\\antigravity-ide\\scratch\\do-aMary\\core\\supabase_client.py', 'a', encoding='utf-8') as f:
    f.write('''
    def get_proyeccion_ventas(self) -> float:
        """Invoca RPC get_proyeccion_ventas_rpc"""
        url = f"{self.url}/rpc/get_proyeccion_ventas_rpc"
        try:
            res = self.session.post(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return float(data) if data is not None else 0.0
            return 0.0
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_proyeccion_ventas: el servidor no responde")
            return 0.0
        except Exception:
            return 0.0

    def get_ajustes_mes(self, mes_actual: str) -> list:
        """Invoca RPC get_ajustes_mes_rpc"""
        url = f"{self.url}/rpc/get_ajustes_mes_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else []
            return []
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_ajustes_mes: el servidor no responde")
            return []
        except Exception:
            return []
''')
