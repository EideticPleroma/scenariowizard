# UNIT Tests

Feature: User Authentication Feature

  Scenario: Successful user login with valid credentials
    Given a registered user with email "user@example.com" and password "ValidPass123!"
    When the user enters email "user@example.com" and password "ValidPass123!"
    And the system validates the credentials against the database
    Then the user is redirected to the dashboard
    And a JWT session token is issued and maintained for 24 hours
    And an audit log entry is created for the successful login

  Scenario: Failed user login with invalid credentials
    Given a registered user with email "user@example.com" and password "ValidPass123!"
    When the user enters email "user@example.com" and password "WrongPass"
    And the system validates the credentials against the database
    Then the user sees an error message "Invalid credentials"
    And no session token is issued
    And an audit log entry is created for the failed login attempt

  Scenario: User login rate limiting after multiple failed attempts
    Given a user attempting login with email "user@example.com"
    When the user fails login 5 times within 15 minutes
    Then the system applies rate limiting and rejects further attempts for 15 minutes
    And the user sees an error message "Too many attempts, try again later"
    And an audit log entry is created for the rate limiting event

  Scenario: User initiates password reset for forgotten password
    Given a registered user with email "user@example.com"
    When the user requests a password reset via email
    Then the system sends a reset link to "user@example.com"
    And the reset link expires after 1 hour
    And an audit log entry is created for the reset request

  Scenario: Successful password reset using valid reset link
    Given a registered user with email "user@example.com" and a valid reset link
    When the user accesses the reset link within 1 hour
    And sets a new password "NewPass123!"
    Then the new password is hashed using bcrypt and updated in the database
    And the user is logged out of all sessions
    And the user receives a confirmation email for successful reset
    And an audit log entry is created for the successful reset

  Scenario: Failed password reset with expired link
    Given a registered user with email "user@example.com" and an expired reset link
    When the user attempts to access the reset link after 1 hour
    Then the system rejects the reset attempt
    And the user sees an error message "Reset link expired"
    And no password change occurs
    And an audit log entry is created for the failed reset attempt

  Scenario: Successful user registration with valid details
    Given no existing user with email "newuser@example.com"
    When the user enters email "newuser@example.com", password "ValidPass123!", and confirm password "ValidPass123!"
    And the system validates the email format
    And the password meets requirements: at least 8 characters with special characters
    And the system checks for no duplicate email
    Then the password is hashed using bcrypt and

# INTEGRATION Tests

Feature: User Authentication Integration Tests

  Background:
    Given the authentication service is running
    And the database is initialized with test data
    And the email service is mocked for integration

  Scenario: Successful user login with valid credentials
    Given a registered user with email "test@example.com" and hashed password exists in the database
    When the user sends a POST request to "/login" with email "test@example.com" and password "ValidPass123!"
    Then the response status is 200
    And a JWT token is returned in the response
    And the user is redirected to the dashboard
    And the session is stored with a 24-hour expiration
    And an audit log entry is created for the successful login
    And the database shows the last login timestamp updated

  Scenario: Failed user login with invalid credentials
    Given a registered user with email "test@example.com" and hashed password exists in the database
    When the user sends a POST request to "/login" with email "test@example.com" and password "InvalidPass"
    Then the response status is 401
    And an error message "Invalid credentials" is returned
    And no JWT token is issued
    And an audit log entry is created for the failed login attempt

  Scenario Outline: Rate limiting on login attempts
    Given a user attempts login <attempts> times with invalid credentials within 15 minutes
    When the user sends another POST request to "/login" with invalid credentials
    Then the response status is 429
    And an error message "Too many login attempts" is returned
    And the rate limit is enforced for the IP address

    Examples:
      | attempts |
      | 5        |
      | 6        |

  Scenario: User initiates password reset from login page
    Given a registered user with email "test@example.com" exists
    When the user sends a POST request to "/forgot-password" with email "test@example.com"
    Then the response status is 200
    And a reset link is sent via email service
    And the reset token is stored in the database with 1-hour expiration
    And an audit log entry is created for the reset request

  Scenario: Successful user registration with valid details
    Given no user with email "newuser@example.com" exists in the database
    When the user sends a POST request to "/register" with email "newuser@example.com", password "StrongPass123!", and confirm password "StrongPass123!"
    Then the response status is 201
    And the password is hashed with bcrypt and stored in the database
    And a confirmation email is sent via email service
    And the account is marked as pending verification in the database
    And an audit log entry is created for the registration

  Scenario Outline: Failed user registration with invalid data
    Given no user with email "<email>" exists in the database
    When the user sends a POST request to "/register" with email "<email>", password "<password>", and confirm password "<confirm_password>"
    Then the response status is 400
    And an error message "<error_message>" is returned
    And no user account is created
    And no confirmation email is sent

    Examples:
      | email                | password      | confirm_password | error_message                    |
      | "invalid-email"      | "StrongPass123!" | "StrongPass123!" | "Invalid email format"          |
      | "user@example.com"   | "weak"        | "weak"           | "Password too weak"              |
      | "user@example.com"   | "StrongPass123!" | "DifferentPass" | "Passwords do not match"        |
