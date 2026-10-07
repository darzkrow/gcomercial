import json
import jwt
from datetime import datetime, timedelta, timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from core.jwt_auth import generate_jwt_tokens
from .models import Aplicativo


class AplicativoJwtAuthenticationTests(TestCase):
    """
    Pruebas rigurosas de seguridad JWT para endpoints de Aplicativos:
    - Obligatoriedad de autenticación en todas las URLs (ninguna pública).
    - Detección y rechazo de tokens vencidos / expirados.
    - Detección y rechazo de tokens alterados o inválidos.
    - Acceso exitoso con token Bearer válido vigente.
    - Filtrado de aplicativos según identidad y grupos AD obtenidos del token.
    """

    def setUp(self):
        self.client = Client()
        self.list_create_url = reverse('aplicativos:aplicativos_list_create')

        # Usuario comercial con grupos de AD
        self.user_comercial = User.objects.create_user(username='carlos.comercial', password='pwd')
        self.user_comercial.profile.department = 'Ventas'
        self.user_comercial.profile.ad_groups = 'GestionComercial_Usuarios, Ventas_Chile'
        self.user_comercial.profile.save()

        # Usuario técnico con grupos de AD
        self.user_ti = User.objects.create_user(username='laura.ti', password='pwd')
        self.user_ti.profile.department = 'Tecnología'
        self.user_ti.profile.ad_groups = 'GestionComercial_Usuarios, Infraestructura_Staff'
        self.user_ti.profile.save()

        # Aplicativos
        self.app_comercial = Aplicativo.objects.create(
            nombre="CRM Ventas Corporativas",
            url="https://crm.empresa.com",
            grupos_ad="Ventas_Chile",
            orden=1
        )
        self.app_ti = Aplicativo.objects.create(
            nombre="Monitor Datacenter",
            url="https://datacenter.empresa.com",
            grupos_ad="Infraestructura_Staff",
            orden=2
        )
        self.app_general = Aplicativo.objects.create(
            nombre="Directorio Telefónico",
            url="https://directorio.empresa.com",
            orden=3
        )

        # Generar tokens válidos
        self.tokens_comercial = generate_jwt_tokens(self.user_comercial)
        self.tokens_ti = generate_jwt_tokens(self.user_ti)

    # --------------------------------------------------------------------------
    # 1. BLOQUEO TOTAL DE URLS SIN AUTENTICAR
    # --------------------------------------------------------------------------
    def test_get_aplicativos_sin_autenticacion_retorna_401(self):
        """Ninguna URL de aplicativos puede ser accedida anónimamente (debe retornar 401)."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload['success'])
        self.assertEqual(payload['code'], "UNAUTHORIZED")

    def test_post_aplicativo_sin_autenticacion_retorna_401(self):
        """Creación de aplicativo sin token debe ser rechazada con 401."""
        response = self.client.post(
            self.list_create_url,
            data=json.dumps({"nombre": "Nuevo Sistema", "url": "https://nuevo.empresa.com"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], "UNAUTHORIZED")

    def test_detalle_aplicativo_sin_autenticacion_retorna_401(self):
        """Consultar detalle sin token debe ser rechazado con 401."""
        detail_url = reverse('aplicativos:aplicativo_detail', kwargs={'pk': self.app_comercial.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], "UNAUTHORIZED")

    def test_delete_aplicativo_sin_autenticacion_retorna_401(self):
        """Eliminación sin token debe ser rechazada con 401."""
        detail_url = reverse('aplicativos:aplicativo_detail', kwargs={'pk': self.app_comercial.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], "UNAUTHORIZED")

    # --------------------------------------------------------------------------
    # 2. TOKENS VENCIDOS Y TOKEN EXPIRADO
    # --------------------------------------------------------------------------
    def test_token_expirado_es_rechazado_con_codigo_token_expired(self):
        """Un token JWT que ha superado su tiempo de vida útil debe ser rechazado con TOKEN_EXPIRED."""
        # Generar un token con 'exp' en el pasado
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        expired_payload = {
            'user_id': self.user_comercial.id,
            'username': self.user_comercial.username,
            'token_type': 'access',
            'iat': int((past_time - timedelta(hours=1)).timestamp()),
            'exp': int(past_time.timestamp()),
        }
        expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        response = self.client.get(
            self.list_create_url,
            HTTP_AUTHORIZATION=f"Bearer {expired_token}"
        )
        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload['success'])
        self.assertEqual(payload['code'], "TOKEN_EXPIRED")

    def test_token_invalido_o_adulterado_retorna_401(self):
        """Un token con firma alterada o formato erróneo debe retornar INVALID_TOKEN."""
        tampered_token = self.tokens_comercial['access_token'] + "fake_signature"
        response = self.client.get(
            self.list_create_url,
            HTTP_AUTHORIZATION=f"Bearer {tampered_token}"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], "INVALID_TOKEN")

    def test_token_refresh_usado_como_access_token_retorna_401(self):
        """No se puede usar un refresh_token para consumir endpoints de la API."""
        refresh_token = self.tokens_comercial['refresh_token']
        response = self.client.get(
            self.list_create_url,
            HTTP_AUTHORIZATION=f"Bearer {refresh_token}"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], "INVALID_TOKEN")

    # --------------------------------------------------------------------------
    # 3. ACCESO CON TOKEN JWT VÁLIDO Y CONTROL POR GRUPOS AD
    # --------------------------------------------------------------------------
    def test_acceso_exitoso_con_jwt_comercial(self):
        """El usuario comercial autenticado con JWT solo ve sus aplicativos autorizados."""
        auth_header = f"Bearer {self.tokens_comercial['access_token']}"
        response = self.client.get(
            self.list_create_url,
            HTTP_AUTHORIZATION=auth_header
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        nombres = [item['nombre'] for item in data['aplicativos']]

        self.assertIn("CRM Ventas Corporativas", nombres)
        self.assertIn("Directorio Telefónico", nombres)
        self.assertNotIn("Monitor Datacenter", nombres)

    def test_acceso_exitoso_con_jwt_ti(self):
        """El usuario de TI autenticado con JWT solo ve aplicativos de TI y generales."""
        auth_header = f"Bearer {self.tokens_ti['access_token']}"
        response = self.client.get(
            self.list_create_url,
            HTTP_AUTHORIZATION=auth_header
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        nombres = [item['nombre'] for item in data['aplicativos']]

        self.assertIn("Monitor Datacenter", nombres)
        self.assertIn("Directorio Telefónico", nombres)
        self.assertNotIn("CRM Ventas Corporativas", nombres)

    def test_detalle_aplicativo_con_jwt_autorizado(self):
        """Consulta exitosa de detalle con Bearer token válido."""
        auth_header = f"Bearer {self.tokens_comercial['access_token']}"
        detail_url = reverse('aplicativos:aplicativo_detail', kwargs={'pk': self.app_comercial.pk})
        response = self.client.get(detail_url, HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['nombre'], "CRM Ventas Corporativas")

    def test_detalle_aplicativo_con_jwt_sin_permisos_retorna_403(self):
        """Si el usuario tiene JWT válido pero no pertenece al grupo AD del aplicativo, recibe 403."""
        # El usuario de TI intenta acceder al aplicativo comercial
        auth_header = f"Bearer {self.tokens_ti['access_token']}"
        detail_url = reverse('aplicativos:aplicativo_detail', kwargs={'pk': self.app_comercial.pk})
        response = self.client.get(detail_url, HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], "PERMISSION_DENIED")

    def test_crear_aplicativo_con_jwt_valido(self):
        """Creación exitosa de aplicativo enviando Bearer token."""
        auth_header = f"Bearer {self.tokens_comercial['access_token']}"
        payload = {
            "nombre": "Portal de Clientes B2B",
            "url": "https://clientes.empresa.com",
            "grupos_ad": ["Ventas_Chile"],
            "orden": 5
        }
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=auth_header
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['data']['nombre'], "Portal de Clientes B2B")

    # --------------------------------------------------------------------------
    # 4. RENOVACIÓN DE TOKEN (REFRESH FLOW)
    # --------------------------------------------------------------------------
    def test_renovacion_exitosa_de_token_con_refresh(self):
        """Permite renovar un token de acceso utilizando el refresh_token."""
        refresh_url = reverse('dashboard:api_refresh_token')
        response = self.client.post(
            refresh_url,
            data=json.dumps({"refresh_token": self.tokens_comercial['refresh_token']}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertIn("access_token", payload['data'])
        self.assertIn("refresh_token", payload['data'])
        self.assertEqual(payload['data']['token_type'], "Bearer")

        # Probar que el nuevo token funcione para acceder a los aplicativos
        nuevo_token = payload['data']['access_token']
        test_resp = self.client.get(self.list_create_url, HTTP_AUTHORIZATION=f"Bearer {nuevo_token}")
        self.assertEqual(test_resp.status_code, 200)
