import unittest

from fastapi import HTTPException

from app.core.auth import _normalized_principal_roles, _principal_from_claims
from app.models.security import PrincipalRole, PrincipalType, TokenClaims


class AuthHelpersTest(unittest.TestCase):
    def test_normalized_principal_roles_maps_known_aliases_and_deduplicates(self) -> None:
        claims = TokenClaims(
            sub="user_demo",
            roles=["realm-admin", "workflow-service-writer", "viewer", "workflow-service-writer"],
        )

        roles = _normalized_principal_roles(claims, PrincipalType.USER)

        self.assertEqual(
            roles,
            [PrincipalRole.PLATFORM_ADMIN, PrincipalRole.OPERATOR, PrincipalRole.OBSERVER],
        )

    def test_principal_from_claims_allows_platform_admin_without_tenant(self) -> None:
        principal = _principal_from_claims(
            TokenClaims(sub="admin_demo", roles=["platform_admin"]),
        )

        self.assertEqual(principal.user_id, "admin_demo")
        self.assertEqual(principal.tenant_id, "")
        self.assertEqual(principal.roles, [PrincipalRole.PLATFORM_ADMIN])

    def test_principal_from_claims_requires_tenant_for_non_platform_admin(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            _principal_from_claims(TokenClaims(sub="reviewer_demo", roles=["reviewer"]))

        self.assertEqual(exc.exception.status_code, 401)
        self.assertIn("Tenant context is required", str(exc.exception.detail))


if __name__ == "__main__":
    unittest.main()
