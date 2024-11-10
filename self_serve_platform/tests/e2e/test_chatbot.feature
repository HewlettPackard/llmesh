Feature: Manual Testing of Chatbot App

    Scenario: Verify changing the project
        Given the Chatbot app is running
        When I post a request to change the project
        And I request the list of project tools
        Then I should manually verify that the correct toolkit is selected for the new project

    Scenario: Verify tool interface
        Given the Chatbot app is running
        When I open the interface modal
        And I select a tool with an interface, like TemperatureFinder in the Meteo Project
        Then I should manually verify that the tool's interface is displayed correctly
        And verify that it is possible to run the tool using the interface

    Scenario: Verify chat interaction
        Given the Chatbot app is running
        When I send a chat message
        Then I should manually verify that the chatbot's response is correct
        And confirm that the correct tool was used to generate the response

    Scenario: Verify error handling when tools are not working
        Given the Chatbot app is running
        And all tools in the project are non-functional
        When I post a chat message
        Then I should manually verify that an appropriate error is reported by the engine related to tool failures

    Scenario: Verify remote memory functionality
        Given the Chatbot app is running
        When I select a project that uses private memory
        And I request the project information
        Then I should manually verify that the chatbot's response includes the correct project description
        And confirm there are no errors in loading or saving messages in memory

    Scenario: Verify error handling when remote memory is not working
        Given the Chatbot app is running
        And the Remote Memory app is not functional
        When I post a chat message
        Then I should manually verify that errors are reported related to loading or saving messages in memory

    Scenario: Verify clearing of chat memories on page refresh
        Given the Chatbot app is running
        And I have active chat sessions in multiple projects
        When I refresh the page
        Then I should manually verify that all chat memories across all projects are cleared
        And any new chat session starts with no previous context
