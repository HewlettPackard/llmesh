Feature: Manual Testing of Backpanel App

    Scenario: Verify Prompt tool data displayed on the app's main interface
        Given the Backpanel app is running
        When I access the app's main data display endpoint
        Then I should manually verify the accuracy of the displayed description
        And I should manually verify the correctness of the displayed arguments
        And I should manually verify the proper configuration of the displayed settings

    Scenario: Verify Prompt toolsystem prompt improvement with LLM
        Given the Backpanel app is running
        And a system prompt is entered in the input field
        When I press the "Improve with LLM" button
        Then I should verify that the system prompt is enhanced or improved by the LLM tool

    Scenario: Verify Prompt tooladding a new interface
        Given the Backpanel app is running
        When I press the "Add Interface" button
        Then I should verify that a new interface is added to the app's main display

    Scenario: Verify Prompt tool arguments reset on Cancel
        Given the Backpanel app is running
        When I modify the arguments via the app's interface
        And I press the "Cancel" button
        Then I should verify that the displayed arguments return to their initial values

    Scenario: Verify Prompt tool reset to default settings functionality
        Given the Backpanel app is running
        When I press the "Reset to Default" button
        Then I should verify that the displayed data and settings return to their default values

    Scenario: Verify Prompt tool settings application to the target tool
        Given the Backpanel app is running
        And target tool settings are configured
        When I press the "Apply" button
        Then I should verify that the settings are correctly applied to the target tool

    Scenario: Verify RAG tool configuration and reimport
        Given the Backpanel app is running
        And the RAG tool is selected from the tool list
        When I choose an extractor from the extractor dropdown
        And I choose a storage backend from the storage dropdown
        And I choose an LLM from the LLM dropdown
        And I set a transformation function
        And I check one or more files for import
        And I set the retrieval prompt
        And I set the chunk size and rerank number
        And I press the "Apply" button
        Then I should verify that the documents are reimported with the new configuration
        And I should verify that retrieval uses the updated settings correctly

    Scenario: Verify Multi-Agent tool prompt and settings display
        Given the Backpanel app is running
        And the Multi-Agent tool is selected
        Then I should see a list of all task prompts
        And I should see the configured LLM for each agent
        And I should see the selected planner type

    Scenario: Verify app stability without running tools
        Given the Backpanel app is running
        And no tools are currently running
        Then I should verify that the app does not crash
        And I should verify that no tools are displayed on the main interface
