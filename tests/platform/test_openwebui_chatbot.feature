Feature: Manual Testing of Chatbot App via Open WebUI

  Scenario: Verify changing the project via model selection
    Given the Chatbot app is running in Open WebUI
    When I select a different model from the model selector dropdown
    Then I should manually verify that the corresponding project's tools and configurations are loaded correctly

  Scenario: Verify chat interaction
    Given the Chatbot app is running in Open WebUI
    When I send a chat message
    Then I should manually verify that the chatbot's response is correct
    And confirm that the appropriate tool was utilized to generate the response

  Scenario: Verify error handling when tools are non-functional
    Given the Chatbot app is running in Open WebUI
    And all tools associated with the selected model are non-functional
    When I send a chat message
    Then I should manually verify that an appropriate error message is reported by the engine indicating tool failures

  Scenario: Verify remote memory functionality
    Given the Chatbot app is running in Open WebUI
    When I select a model associated with a project that uses private memory
    And I request the project information
    Then I should manually verify that the chatbot's response includes the correct project description
    And confirm there are no errors in loading or saving messages in memory

  Scenario: Verify error handling when remote memory is non-functional
    Given the Chatbot app is running in Open WebUI
    And the Remote Memory service is non-functional
    When I send a chat message
    Then I should manually verify that errors are reported related to loading or saving messages in memory

  Scenario: Verify chat history continuity across model changes
    Given the Chatbot app is running in Open WebUI
    And I have an ongoing chat session
    When I switch to a different model within the same chat session
    Then I should manually verify that the chatbot retains the previous messages in context
    And confirm that the conversation continues seamlessly with the new model
