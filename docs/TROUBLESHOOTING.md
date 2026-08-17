# Troubleshooting & FAQ

- **Containers failing to start**: Verify port 80 and 8000 are not occupied by running `lsof -i :80`.
- **Database Connection Error**: Verify `DATABASE_URL` matches your container IP.
