Feature: Manual Testing of OpenAPI Agents Tool

    Scenario: Verify the manifest endpoint
        Given the OpenAPI Agents tool is running
        When I navigate to its manifest endpoint
        Then I should manually verify that the manifest output adheres to the expected structure and contains all required content

    Scenario: Verify the OpenAPI search information endpoint
        Given the OpenAPI Agents tool is running
        When I submit a query to retrieve information related to the request body example for the N5 interface configuration
        Then I should manually verify that the output includes the correct request body details formatted as a JSON object
