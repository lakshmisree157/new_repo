# TODO: Fix adopter_id and user_id clashes in adoption endpoints

## Tasks
- [x] Update `get_requests_by_adopter` in `backend/controllers/adoption_controller.py` to expect user_id only and find adopter by user_id
- [x] Change route `/adopter/<int:adopter_id>/requests` to `/user/<int:user_id>/requests` in `backend/routes/adoption_routes.py` and restrict to adopter role
- [x] Ensure MongoDB ObjectId validation in `create_adoption_request` is robust
- [ ] Test the changes by running the app and checking endpoints

## Notes
- Standardize on user_id for adopter operations since JWT provides user_id
- Avoid ID clashes by not mixing adopter_id and user_id in the same function
- MongoDB part: animal_mongo_id is properly validated as ObjectId
