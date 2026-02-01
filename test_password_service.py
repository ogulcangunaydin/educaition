from app.services.password_service import (
    validate_password_strength, 
    hash_password, 
    verify_password, 
    PasswordValidationError,
    check_password_strength
)

print('Testing weak passwords:')
for pwd in ['123', 'password', 'Password1', 'password1!']:
    valid, errors = validate_password_strength(pwd)
    print(f'{pwd}: Valid={valid}, Errors={errors}')

print('\nTesting strong password:')
strong_pwd = 'MySecure@123'
valid, errors = validate_password_strength(strong_pwd)
print(f'{strong_pwd}: Valid={valid}')

print('\nTesting password strength levels:')
test_passwords = ['abc', 'Password1!', 'MyVerySecure@12345']
for pwd in test_passwords:
    strength = check_password_strength(pwd)
    print(f'{pwd}: {strength.value}')

print('\nTesting password hashing:')
hashed = hash_password(strong_pwd)
print(f'Hashed length: {len(hashed)}')
print(f'Verify correct: {verify_password(strong_pwd, hashed)}')
print(f'Verify wrong: {verify_password("wrong", hashed)}')

print('\nTesting PasswordValidationError:')
try:
    hash_password('weak')
except PasswordValidationError as e:
    print(f'Caught error with {len(e.errors)} issues: {e.errors}')

print('\nAll tests passed!')
