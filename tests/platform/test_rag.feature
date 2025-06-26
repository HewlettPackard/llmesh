Feature: Manual Testing of Document RAG Tool

    Scenario: Verify the manifest endpoint
        Given the Document RAG tool is running
        When I navigate to its manifest endpoint
        Then I should manually verify that the manifest output adheres to the expected structure and includes all necessary content

    Scenario: Verify document loading and information retrieval
        Given the Document RAG tool is running
        When I configure the tool to load a document and reset the database
        And I submit a query to retrieve information related to PCSCF discovery
        Then I should manually verify that the document is successfully loaded into ChromaDB
        And I should manually verify that the tool responds with accurate information, correctly pointing to the relevant section of the document

    Scenario: Verify information retrieval from a loaded document
        Given the Document RAG tool is running
        When I submit a query to retrieve information related to PCSCF discovery
        Then I should manually verify that the tool provides accurate information, correctly pointing to the relevant section of the document
