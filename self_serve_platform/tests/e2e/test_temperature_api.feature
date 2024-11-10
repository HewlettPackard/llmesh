Feature: Manual Testing of Temperature API Tool

    Scenario: Verify the manifest endpoint
        Given the Temperature API tool is running
        When I navigate to its manifest endpoint
        Then I should manually verify that the manifest output matches the expected structure and content

    Scenario: Verify the temperature retrieval endpoint
        Given the Temperature API tool is running
        When I submit a valid longitude and latitude to the temperature retrieval endpoint
        Then I should manually verify that the output correctly reflects the current temperature for the specified location
