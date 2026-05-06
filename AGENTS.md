# tagmate

Deployment pattern context.

- Standardize tagmate-style deploys across projects.
- GitHub Actions copies the repo to the Docker server, renders the deploy env file from a template, and restarts the service with `docker compose`.
- No registry unless a repo explicitly needs one.
- Keep env in `.env` files and Traefik config in compose labels.
