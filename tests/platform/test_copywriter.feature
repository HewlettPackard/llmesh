Feature: Manual Testing of Copywriter Tool

    Scenario: Verify the manifest endpoint
        Given the Copywriter tool is running
        When I navigate to its manifest endpoint
        Then I should manually verify that the output matches the expected manifest

    Scenario: Verify the text improvement endpoint
        Given the Copywriter tool is running
        When I submit a text to the tool's improvement endpoint
        Then I should manually verify that the output is an improved version of the text with an explanation
