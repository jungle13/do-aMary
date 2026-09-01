"""
core/periodo_manager.py
Gestor global del estado y contexto de período para toda la aplicación.
"""
import calendar
import datetime
from core.database import BaseDatabase
from core.logger import get_logger, log_error

logger = get_logger("PeriodoManager")


class PeriodoManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PeriodoManager, cls).__new__(cls)
            cls._instance._inicializado = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_inicializado", False):
            return
        self.db = BaseDatabase()
        self.periodo_seleccionado = None  # e.g. "2026-08" or "2026-09"
        self.periodos_disponibles = []
        self.listeners = []
        self._inicializado = True
        self.cargar_periodos()

    def cargar_periodos(self) -> list:
        """Carga los periodos de Supabase y asegura que el mes actual esté en la lista."""
        try:
            res = self.db.get("periodos_inventario?select=*&order=mes_periodo.desc", timeout=10)
            periodos = res.json() if (res and res.status_code == 200) else []
            
            hoy = datetime.date.today()
            mes_hoy = hoy.strftime("%Y-%m")
            
            meses_existentes = [p.get("mes_periodo") for p in periodos if p.get("mes_periodo")]
            if mes_hoy not in meses_existentes:
                periodos.insert(0, {
                    "id_periodo": "temp-" + mes_hoy,
                    "mes_periodo": mes_hoy,
                    "estado": "ABIERTO",
                    "fecha_inicio": f"{mes_hoy}-01"
                })
            
            self.periodos_disponibles = periodos
            
            if not self.periodo_seleccionado:
                abiertos = [p for p in periodos if p.get("estado") == "ABIERTO"]
                if abiertos:
                    self.periodo_seleccionado = abiertos[0].get("mes_periodo")
                elif periodos:
                    self.periodo_seleccionado = periodos[0].get("mes_periodo")
                else:
                    self.periodo_seleccionado = mes_hoy
            return self.periodos_disponibles
        except Exception as ex:
            log_error("PeriodoManager.cargar_periodos", ex)
            if not self.periodo_seleccionado:
                self.periodo_seleccionado = datetime.date.today().strftime("%Y-%m")
            return self.periodos_disponibles

    def get_periodo_activo(self) -> str:
        if not self.periodo_seleccionado:
            self.cargar_periodos()
        return self.periodo_seleccionado or datetime.date.today().strftime("%Y-%m")

    def get_estado_periodo(self, mes: str | None = None) -> str:
        target = mes or self.get_periodo_activo()
        for p in self.periodos_disponibles:
            if p.get("mes_periodo") == target:
                return str(p.get("estado") or "ABIERTO").upper()
        return "ABIERTO"

    def get_info_periodo(self, mes: str | None = None) -> dict:
        target = mes or self.get_periodo_activo()
        for p in self.periodos_disponibles:
            if p.get("mes_periodo") == target:
                return p
        return {"mes_periodo": target, "estado": "ABIERTO"}

    def get_rango_fechas(self, mes: str | None = None) -> tuple[str, str]:
        target = mes or self.get_periodo_activo()
        try:
            year, month = map(int, target.split("-"))
            last_day = calendar.monthrange(year, month)[1]
            return f"{target}-01", f"{target}-{last_day:02d}"
        except Exception:
            return f"{target}-01", f"{target}-28"

    def get_fecha_corte(self, mes: str | None = None) -> str:
        """Devuelve la fecha de corte final del periodo (o fecha de hoy si es el mes en curso)."""
        target = mes or self.get_periodo_activo()
        hoy = datetime.date.today()
        if target == hoy.strftime("%Y-%m"):
            return hoy.strftime("%Y-%m-%d")
        _, f_fin = self.get_rango_fechas(target)
        return f_fin

    @staticmethod
    def formatear_nombre_mes(mes_str: str) -> str:
        """Convierte '2026-08' a 'Agosto 2026'."""
        try:
            partes = str(mes_str).strip().split("-")
            nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                       "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            m_idx = int(partes[1]) - 1
            return f"{nombres[m_idx]} {partes[0]}"
        except Exception:
            return str(mes_str)

    def set_periodo_activo(self, nuevo_periodo: str, notify_source=None):
        if self.periodo_seleccionado != nuevo_periodo:
            self.periodo_seleccionado = nuevo_periodo
            logger.info(f"Periodo global cambiado a: {nuevo_periodo}")
            self._notificar_listeners(notify_source)

    def subscribe(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def _notificar_listeners(self, source=None):
        for listener in list(self.listeners):
            try:
                listener(self.periodo_seleccionado, source)
            except Exception as ex:
                logger.warning(f"Error notificando listener de periodo: {ex}")
