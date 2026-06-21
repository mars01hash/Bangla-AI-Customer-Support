# Pre-seeded Demo Accounts

These accounts are created automatically on first startup. Use them to explore the platform without any setup.

## Accounts

| Role | Email | Password | Access |
|---|---|---|---|
| Super Admin | `super@platform.com` | `superpassword123` | Full platform — all tenants, all users |
| Store Admin (ShopBD) | `admin@shopbd.com` | `storepassword123` | ShopBD tenant only |
| Store Admin (FashionBD) | `admin@fashionbd.com` | `storepassword123` | FashionBD tenant only |
| Agent (ShopBD) | `agent@shopbd.com` | `agentpassword123` | ShopBD tickets only |
| Legacy Admin | `admin@example.com` | `adminpassword123` | Alias for super_admin |
| Legacy Agent | `agent@example.com` | `agentpassword123` | ShopBD tickets |

## Login Auto-Routing

The login page auto-redirects after authentication based on role:

| Role | Redirects to |
|---|---|
| `super_admin` | `/superadmin` |
| `store_admin` | `/storeadmin` |
| `agent` | `/dashboard` |
| `customer` | `/` (storefront) |

The login page also includes one-click **demo shortcut buttons** so you can jump into any role without typing credentials.

!!! warning "Change passwords in production"
    These credentials are for development only. Set strong passwords and rotate the `JWT_SECRET` before deploying to a public server.
