from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIOrganizationsInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Organizations API.
    Reference: https://platform.openai.com/docs/api-reference/organizations
    """

    def list_organizations(self) -> dict:
        """
        List all organizations.
        GET /v1/organizations
        """
        try:
            response = self.client.organizations.list()
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_organization(self, organization_id: str) -> dict:
        """
        Retrieve an organization by ID.
        GET /v1/organizations/{organization_id}
        """
        try:
            response = self.client.organizations.retrieve(organization_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_memberships(self, organization_id: str) -> dict:
        """
        List all memberships in an organization.
        GET /v1/organizations/{organization_id}/memberships
        """
        try:
            response = self.client.organizations.list_memberships(organization_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_organizations(self) -> dict:
        """
        Async: List all organizations.
        GET /v1/organizations
        """
        try:
            response = await self.client.organizations.list()
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_organization(self, organization_id: str) -> dict:
        """
        Async: Retrieve an organization by ID.
        GET /v1/organizations/{organization_id}
        """
        try:
            response = await self.client.organizations.retrieve(organization_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_memberships(self, organization_id: str) -> dict:
        """
        Async: List all memberships in an organization.
        GET /v1/organizations/{organization_id}/memberships
        """
        try:
            response = await self.client.organizations.list_memberships(organization_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)
