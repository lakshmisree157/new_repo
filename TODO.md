# TODO: Fix Pet Adoption System Issues

## Issues to Fix
1. **Adding veterinary records fails** - Debug and fix vet record addition.
2. **Adopter page: Display age alongside center name in dog details** - Update adopter-dashboard.html to show age in dog cards.
3. **Updating profile not working** - Add PATCH /api/auth/profile route in auth_routes.py.
4. **Accept/reject buttons not disabling after approval** - Ensure buttons disable after status update in center-dashboard.html.
5. **Dog not updated in MongoDB when adopted** - Set animal.is_adopted = True when request approved in adoption_controller.py.
6. **Center page not updating automatically** - Reload dogs list after request status update in center-dashboard.html.

## Implementation Steps
- [x] Add PATCH /api/auth/profile route in backend/routes/auth_routes.py
- [x] Modify update_request_status in backend/controllers/adoption_controller.py to update animal.is_adopted
- [x] Update center-dashboard.html to reload dogs after request status update
- [x] Update adopter-dashboard.html to add age to dog cards
- [x] Debug vet record addition: Check form data and API call in center-dashboard.html
- [x] Ensure request buttons disable after approval by re-rendering requests
- [x] Test all changes
