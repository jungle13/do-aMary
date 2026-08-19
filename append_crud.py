
with open("core/supabase_client.py", "a", encoding="utf-8") as f:
    f.write('''

    # --- CRUD COMPRAS INDIVIDUALES ---
    def update_compra_individual(self, id_compra, datos):
        """Actualiza un registro de compra individual por su UUID."""
        try:
            url = f"{self.url}/registro_compras?id_compra=eq.{id_compra}"
            res = self.session.patch(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en update_compra_individual: {ex}")
            return False

    def eliminar_compra_individual(self, id_compra):
        """Elimina un registro de compra individual de Supabase."""
        try:
            url = f"{self.url}/registro_compras?id_compra=eq.{id_compra}"
            res = self.session.delete(url, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en eliminar_compra_individual: {ex}")
            return False

    # --- CRUD VENTAS INDIVIDUALES ---
    def insert_venta_individual(self, datos):
        """Crea un registro de venta individual en Supabase."""
        try:
            url = f"{self.url}/registro_ventas"
            res = self.session.post(url, json=[datos], headers=self.headers, timeout=10)
            return res.status_code in (200, 201)
        except Exception as ex:
            print(f"Error en insert_venta_individual: {ex}")
            return False

    def update_venta_individual(self, id_venta, datos):
        """Actualiza un registro de venta individual por su UUID."""
        try:
            url = f"{self.url}/registro_ventas?id_venta=eq.{id_venta}"
            res = self.session.patch(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en update_venta_individual: {ex}")
            return False

    def eliminar_venta_individual(self, id_venta):
        """Elimina un registro de venta individual de Supabase."""
        try:
            url = f"{self.url}/registro_ventas?id_venta=eq.{id_venta}"
            res = self.session.delete(url, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en eliminar_venta_individual: {ex}")
            return False
''')
