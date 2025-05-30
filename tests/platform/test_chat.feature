Feature: Manual Testing of Chat Service Tool

    Scenario: Verify the manifest endpoint
        Given the Chat Service tool is running
        When I navigate to its manifest endpoint
        Then I should manually verify that the output matches the expected manifest

    Scenario: Verify default assistant response
        Given the Chat Service tool is running
        When I submit a query without specifying a persona
        Then I should manually verify that the assistant responds using the default professional tone

    Scenario: Verify persona-based response
        Given the Chat Service tool is running
        When I submit a query with the persona set to "pirate"
        Then I should manually verify that the response reflects the pirate-style language and tone

    Scenario: Verify memory behavior across interactions
        Given the Chat Service tool is running
        When I submit a query with memory enabled
        And I submit a follow-up query with memory still active
        Then I should manually verify that the assistant uses prior context in its response

    Scenario: Verify fallback on unknown persona
        Given the Chat Service tool is running
        When I submit a query with a non-existing persona
        Then I should manually verify that the assistant falls back to the default system prompt

    Scenario: Verify new conversation clears memory
        Given the Chat Service tool is running
        When I start a new conversation with the "new" flag enabled
        Then I should manually verify that previous context is no longer used in the assistant's response
