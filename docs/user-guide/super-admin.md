# Super Admin Panel

**Route:** `/superadmin`  
**Login:** `super@platform.com` / `superpassword123`

The super admin owns the entire platform and manages all store tenants.

## Capabilities

| Action | Description |
|---|---|
| View all tenants | List every registered store with status, API key preview, and stats |
| Create tenant | Generates a new store with a unique API key |
| Activate / deactivate | Toggle a store on or off without deleting it |
| Rotate API key | Issues a new key and invalidates the old one instantly |
| View all users | See every user across all stores with their role and store assignment |
| Update any user | Change a user's role or reassign them to a different store |

## Creating a New Tenant

1. Click **New Tenant** in the Super Admin Panel
2. Enter the store name
3. The platform generates a unique `sk_...` API key automatically
4. Share the API key with the store admin — they paste it into their widget embed code

## Rotating an API Key

1. Find the tenant in the tenant list
2. Click **Rotate Key**
3. The new key is shown once — copy it immediately
4. Any widget still using the old key will receive `401 Unauthorized` responses until updated
