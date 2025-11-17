# Architecture Notes

- Authentication: JWT-based; roles: `admin`, `adoption_center`, `adopter`.
- Data: MySQL for relational data (users, pets, adoptions), MongoDB for flexible documents (optional metadata & ML). 
- ML: `ml_model` folder will contain training scripts, datasets, and serialized models.
- API surface: `backend/routes` should expose REST endpoints under `/api/*`.

Future: add CI, Docker, and more tests.
