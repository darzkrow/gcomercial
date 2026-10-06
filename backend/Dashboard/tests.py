import json
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from Dashboard.models import UserProfile
from core.authentication import ActiveDirectoryBackend


class UserProfileAndADTests(TestCase):

    def test_user_profile_automatically_created_on_user_creation(self):
        """Verifica que al crear un usuario en Django, su UserProfile se cree automáticamente."""
        user = User.objects.create_user(
            username='carlos.perez',
            email='carlos.perez@empresa.com',
            first_name='Carlos',
            last_name='Perez'
        )
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
        self.assertEqual(str(user.profile), "Perfil de Carlos Perez")

    def test_extract_cn_from_dn(self):
        """Verifica la extracción limpia del Common Name de Distinguished Names de AD."""
        backend = ActiveDirectoryBackend()
        self.assertEqual(backend._extract_cn("CN=Ventas,OU=Grupos,DC=empresa,DC=local"), "Ventas")
        self.assertEqual(backend._extract_cn("cn=GPO_AccesoSistemas,ou=GPO,dc=empresa,dc=local"), "GPO_AccesoSistemas")
        self.assertEqual(backend._extract_cn("SimpleGroupName"), "SimpleGroupName")
        self.assertEqual(backend._extract_cn(""), "")

    @override_settings(LDAP_ENABLED=False)
    def test_backend_returns_none_when_disabled(self):
        """Si LDAP está deshabilitado en .env, el backend debe retornar None sin intentar conectar."""
        backend = ActiveDirectoryBackend()
        result = backend.authenticate(None, username='usuario_test', password='password123')
        self.assertIsNone(result)

    def test_user_profile_fields_update(self):
        """Verifica que los atributos de perfil (cargo, departamento, teléfono, etc.) se persistan correctamente."""
        user = User.objects.create_user(username='maria.gomez')
        profile = user.profile
        profile.department = 'Finanzas'
        profile.job_title = 'Analista Contable'
        profile.phone = '+56 9 1234 5678'
        profile.ad_dn = 'CN=Maria Gomez,OU=Usuarios,DC=empresa,DC=local'
        profile.ad_groups = 'GestionComercial_Usuarios, Finanzas_Staff'
        profile.save()

        profile.refresh_from_db()
        self.assertEqual(profile.department, 'Finanzas')
        self.assertEqual(profile.job_title, 'Analista Contable')
        self.assertEqual(profile.phone, '+56 9 1234 5678')
        self.assertIn('GestionComercial_Usuarios', profile.ad_groups)


class RestApiViewsTests(TestCase):
    """Pruebas unitarias para todas las Vistas Basadas en Funciones (FBVs) de la API REST."""

    def setUp(self):
        self.client = Client()
        self.password = "SecurePass123!"
        self.user = User.objects.create_user(
            username='ana.lopez',
            email='ana.lopez@empresa.com',
            password=self.password,
            first_name='Ana',
            last_name='Lopez'
        )
        self.user.profile.department = 'Ventas'
        self.user.profile.phone = '+56 9 9999 8888'
        self.user.profile.save()

        # Usuario Staff para pruebas de permisos
        self.staff_user = User.objects.create_user(
            username='admin.user',
            email='admin@empresa.com',
            password=self.password,
            is_staff=True
        )

    def test_health_check(self):
        """El endpoint health debe responder 200 y status 'healthy'."""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'healthy')

    def test_login_success(self):
        """Login exitoso con usuario local retorna 200, datos de usuario y su perfil."""
        response = self.client.post(
            '/api/v1/auth/login/',
            data=json.dumps({'username': 'ana.lopez', 'password': self.password}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['username'], 'ana.lopez')
        self.assertEqual(data['data']['user']['profile']['department'], 'Ventas')

    def test_login_missing_credentials(self):
        """Login sin password o username debe retornar 400."""
        response = self.client.post(
            '/api/v1/auth/login/',
            data=json.dumps({'username': 'ana.lopez'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], 'MISSING_CREDENTIALS')

    def test_login_invalid_credentials(self):
        """Login con credenciales incorrectas debe retornar 401."""
        response = self.client.post(
            '/api/v1/auth/login/',
            data=json.dumps({'username': 'ana.lopez', 'password': 'WrongPassword!'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], 'INVALID_CREDENTIALS')

    def test_me_endpoint_requires_auth(self):
        """Consultar /api/v1/auth/me/ sin sesión activa debe retornar 401."""
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], 'UNAUTHORIZED')

    def test_me_endpoint_authenticated(self):
        """Consultar /api/v1/auth/me/ con sesión debe retornar los datos del usuario."""
        self.client.login(username='ana.lopez', password=self.password)
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['user']['username'], 'ana.lopez')

    def test_profile_get_and_update(self):
        """GET y PUT a /api/v1/profile/ deben permitir consultar y actualizar teléfono y nombres."""
        self.client.login(username='ana.lopez', password=self.password)

        # GET
        res_get = self.client.get('/api/v1/profile/')
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()['data']['profile']['phone'], '+56 9 9999 8888')

        # PUT
        res_put = self.client.put(
            '/api/v1/profile/',
            data=json.dumps({'phone': '+56 9 1111 2222', 'first_name': 'Anita'}),
            content_type='application/json'
        )
        self.assertEqual(res_put.status_code, 200)

        # Validar persistencia
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Anita')
        self.assertEqual(self.user.profile.phone, '+56 9 1111 2222')

    def test_dashboard_stats(self):
        """/api/v1/dashboard/stats/ debe calcular métricas de usuarios y departamentos."""
        self.client.login(username='ana.lopez', password=self.password)
        response = self.client.get('/api/v1/dashboard/stats/')
        self.assertEqual(response.status_code, 200)
        stats = response.json()['data']
        self.assertGreaterEqual(stats['users']['total'], 2)
        self.assertIn('departments', stats)
        self.assertEqual(stats['system']['api_version'], 'api/v1')

    def test_users_list_staff_permission(self):
        """/api/v1/users/ exige ser Staff (403 para usuarios normales, 200 para Staff)."""
        # Usuario normal -> 403 Forbidden
        self.client.login(username='ana.lopez', password=self.password)
        res_user = self.client.get('/api/v1/users/')
        self.assertEqual(res_user.status_code, 403)

        # Usuario Staff -> 200 OK
        self.client.login(username='admin.user', password=self.password)
        res_staff = self.client.get('/api/v1/users/')
        self.assertEqual(res_staff.status_code, 200)
        data = res_staff.json()['data']
        self.assertIn('users', data)
        self.assertIn('pagination', data)

    def test_logout(self):
        """/api/v1/auth/logout/ finaliza la sesión activa del usuario."""
        self.client.login(username='ana.lopez', password=self.password)
        res_logout = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(res_logout.status_code, 200)

        # La siguiente petición protegida debe rechazar con 401
        res_me = self.client.get('/api/v1/auth/me/')
        self.assertEqual(res_me.status_code, 401)
