Feature: Manual Testing of Agentic Memory App

    Scenario: Verify saving a personal message
        Given the Agentic Memory app is running
        When I post a personal message to the app
        Then I should manually verify that the message is correctly stored in the personal memory

    Scenario: Verify saving a project message
        Given the Agentic Memory app is running
        When I post a project-related message to the app
        Then I should manually verify that the message is correctly stored in the project memory

    Scenario: Verify loading messages
        Given the Agentic Memory app is running
        When I request to load messages from the app
        Then I should manually verify that the API correctly returns the stored messages

    Scenario: Verify clearing all messages
        Given the Agentic Memory app is running
        When I send a request to clear all messages
        Then I should manually verify that all messages have been successfully cleared from the memory
