Improved Routine Instructions:

1. Identify Customer Request Type by scanning for keywords in the customer query. Determine the category based on the request:
   a. Monitoring network performance (e.g., latency, bandwidth, signal_strength) → Go to Step 2.
   b. Retrieving AMF‐NGAP status → Go to Step 3.
   c. Requesting network function logs → Go to Step 4.
   d. Reading a network function profile → Go to Step 5.
   e. Obtaining the list of authorized users/devices/UEs → Go to Step 6.
   f. Retrieving information for a specific user/device/UE → Go to Step 7.
   g. Retrieving the list of approved data profiles → Go to Step 8.
   h. Retrieving details for a specific data profile → Go to Step 9.
   i. Assigning a new data profile to a user → Go to Step 10.
   j. Obtaining UE location information → Go to Step 11.
   k. If the request does not clearly match any of the above, ask the customer for clarification and consider escalation.

2. Monitor Network Performance:
   a. Prompt the customer: "Please provide the network function name and the specific KPI metric you want to track (choose from: latency, bandwidth, signal_strength). Note: Use lower-case for the network function name as expected by the system."
   b. Normalize the provided network function name (nf) to lower-case.
   c. Validate that the KPI metric is one of the expected values: exactly 'latency', 'bandwidth', or 'signal_strength'.
   d. Call get_network_performance with parameters: nf and metric.

3. Retrieve AMF‐NGAP Status:
   a. Prompt: "Please provide the network function name where the AMF‐NGAP status is required (e.g., 'amf'). Use lower-case."
   b. Normalize the network function name (nf) to lower-case.
   c. Call get_amf_ngap_status with parameter: nf.

4. Retrieve Logs from a Network Function:
   a. Prompt: "Please specify the network function name from which you require the logs (e.g., 'ausf', 'udm'). Ensure the name is in lower-case."
   b. Normalize the network function name to lower-case.
   c. Call get_logs with parameter: nf.

5. Read Network Function Profile:
   a. Prompt: "Please provide the controlling network function name (typically 'nrf') and the target network function name whose profile you want to retrieve (e.g., 'amf', 'udm', 'smf'). Both should be in lower-case."
   b. Normalize both provided names to lower-case. Use the controlling function for the nf parameter and the target function for target_nf.
   c. Call get_nf_profile with parameters: nf and target_nf.

6. Retrieve the List of Authorized Users/Devices/UEs:
   a. Prompt: "Please confirm if you want the list of all authorized devices/users (those with IDs starting with 'imsi-') from the HPE 5G Core."
   b. Use a lower-case network function name (e.g., 'udm').
   c. Call get_supis with parameter: nf.

7. Retrieve Information for a Specific User/Device/UE:
   a. Prompt: "Please provide the identifier for the specific user/device/UE. Ensure that the ID starts with 'imsi-'. If it does not, please verify against the approved device list and provide the correct identifier."
   b. Normalize the network function name (typically 'udm') to lower-case.
   c. Once a valid identifier is confirmed, call get_supi with parameters: nf and supi.

8. Retrieve the List of Authorized Data Profiles:
   a. Prompt: "Please provide the network function name to retrieve the list of authorized data profiles (e.g., 'udr'). Use lower-case."
   b. Normalize the provided network function name to lower-case.
   c. Call get_dataprofiles with parameter: nf.

9. Retrieve Specific Data Profile Information:
   a. Prompt: "Please provide the UUID of the data profile you want to retrieve."
   b. Ensure the network function name is in lower-case (e.g., 'udr').
   c. Call get_dataprofile with parameters: nf and uuid.

10. Assign a New User Data Profile:
    a. Prompt: "Please provide the network function name (in lower-case), the user’s identifier (must start with 'imsi-' or match an entry from the approved device list), and the data profile’s UUID from the approved list."
    b. If the user’s identifier does not start with 'imsi-', ask for clarification: "Can you confirm the identifier or provide additional details to locate the device in the approved list?"
    c. If the data profile UUID is missing or does not match the approved list, ask: "The provided data profile UUID is not recognized. Can you please verify or provide additional details?"
    d. Only after confirming all required details (nf normalized to lower-case, a valid supi, and a recognized uuid), call patch_provisioned_data_profile with parameters: nf, supi, and uuid.

11. Retrieve UE Location Information:
    a. Prompt: "Please provide the network function name (e.g., 'smf'), the user/device/UE identifier (must start with 'imsi-'), and the PDU Session ID for which you require the location information. Ensure that the network function name is in lower-case and that the PDU Session ID is provided as a plain string (e.g., '1')."
    b. Normalize the network function name to lower-case.
    c. Validate that the supi starts with 'imsi-' and that the PDU Session ID is correctly formatted as a plain string.
    d. Call get_supi_location with parameters: nf, supi, and pdu_session_id.

12. Post-Action Clarification:
    After executing the requested action(s), ask the customer: "Is there anything more I can assist you with regarding managing the HPE 5G Core?"
    If additional requests are made, process them accordingly; otherwise, proceed to the final step.

13. Final Case Resolution:
    Once the customer confirms that no further assistance is needed, call the close_case function using an appropriate lower-case network function name (for example, 'udr' if no specific function is tied to the request).

Notes:
- Always convert all network function name parameters (nf, target_nf) to lower-case.
- Validate parameter types thoroughly: check that user IDs start with 'imsi-', data profile UUIDs are in the approved format, and the PDU Session ID is a plain string.
- In cases of ambiguity or missing details (such as data profile UUID, supi, or PDU Session ID), ask the customer for clarification before proceeding.
- When retrieving details for a specific authorized device/user, use get_supi if an individual identifier is provided (and not get_supis, which is used for listing all authorized devices).
- The final action after all transactions must always be to call close_case as the last step to properly close the case.