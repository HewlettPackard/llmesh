Feature: Manual Testing of Temperature Analyzer Tool

    Scenario: Verify the manifest endpoint
        Given the Temperature Analyzer tool is running
        When I navigate to its manifest endpoint
        Then I should manually verify that the manifest output conforms to the expected structure and content

    Scenario: Verify the temperature analysis endpoint
        Given the Temperature Analyzer tool is running
        When I submit a query to retrieve the maximum temperature in Italy over the last 5 years from the dataset
        Then I should manually verify that the output includes the correct analysis code
        And I should manually verify that the output contains a binary image representing the analysis results
