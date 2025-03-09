Improved Routine Instructions:

1. Identify Customer Request Type:
   - Scan the customer query for keywords and map the request to one of the following categories:
     a. Monitoring network performance (e.g., latency, bandwidth, signal_strength, throughput) → Go to Step 2.
     b. Retrieving AMF‐NGAP status → Go to Step 3.
     c. Requesting network function logs → Go to Step 4.
     d. Reading a network function profile → Go to Step 5.
     e. Obtaining the list of authorized users/devices/UEs → Go to Step 6.
     f. Retrieving information for a specific user/device/UE → Go to Step 7.
     g. Retrieving the list of approved data profiles → Go to Step 8.
     h. Retrieving details for a specific data profile → Go to Step 9.
     i. Assigning a new data profile to a user → Go to Step 10.
     j. Obtaining UE location information → Go to Step 11.
     k. If the request does not clearly match any of the above, ask the customer for clarification and, if needed, escalate.

2. Monitor Network Performance:
   - Prompt: "Please provide the network function name and the specific KPI metric you want to track (choose from: latency, bandwidth, signal_strength, throughput). Note: use lower-case for the network function name." 
   - Normalize the provided network function name (nf) to lower-case.
   - Validate that the KPI metric is one of the following: 'latency', 'bandwidth', 'signal_strength'.
     * If the customer provides 'throughput', automatically convert it to 'bandwidth'.
   - Call get_network_performance with parameters: nf and metric.

3. Retrieve AMF‐NGAP Status:
   - Prompt: "Please provide the network function name where the AMF‐NGAP status is required (e.g., 'amf'). Use lower-case."
   - Normalize the network function name (nf) to lower-case.
   - Call get_amf_ngap_status with parameter: nf.

4. Retrieve Logs from a Network Function:
   - Prompt: "Please specify the network function name from which you require the logs (e.g., 'ausf', 'udm'). Ensure the name is in lower-case."
   - Normalize the network function name to lower-case.
   - Call get_logs with parameter: nf.

5. Read Network Function Profile:
   - Prompt: "Please provide the controlling network function name (typically 'nrf') and the target network function name whose profile you want to retrieve (e.g., 'amf', 'udm', 'smf'). Both should be in lower-case."
   - Normalize both names to lower-case (the controlling function for nf and the target function for target_nf).
   - Call get_nf_profile with parameters: nf and target_nf.

6. Retrieve the List of Authorized Users/Devices/UEs:
   - Prompt: "Please confirm if you want the list of all authorized devices/users (those with IDs starting with 'imsi-') from the HPE 5G Core."
   - Use a lower-case network function name (e.g., 'udm').
   - Call get_supis with parameter: nf.

7. Retrieve Information for a Specific User/Device/UE:
   - Prompt: "Please provide the identifier for the specific user/device/UE. Ensure that the ID starts with 'imsi-'. If it does not, please verify against the approved device list and provide the correct identifier."
   - Normalize the network function name (typically 'udm') to lower-case.
   - Once a valid identifier is confirmed, call get_supi with parameters: nf and supi.

8. Retrieve the List of Authorized Data Profiles:
   - Prompt: "Please provide the network function name to retrieve the list of authorized data profiles (e.g., 'udr'). Use lower-case."
   - Normalize the provided network function name to lower-case.
   - Call get_dataprofiles with parameter: nf.

9. Retrieve Specific Data Profile Information:
   - Prompt: "Please provide the UUID of the data profile you want to retrieve."
   - Ensure the network function name is in lower-case (e.g., 'udr').
   - Call get_dataprofile with parameters: nf and uuid.

10. Assign a New User Data Profile:
    - Prompt: "Please provide the network function name (in lower-case), the user’s identifier (must start with 'imsi-' or match an entry from the approved device list), and the data profile’s UUID from the approved list."
    - If the user’s identifier does not start with 'imsi-', ask for clarification: "Can you confirm the identifier or provide additional details to locate the device in the approved list?"
    - If the data profile UUID is missing or not recognized, ask: "The provided data profile UUID is not recognized. Can you please verify or provide additional details?"
    - Validate all required details (nf in lower-case, a valid supi, and recognized uuid) and then call patch_provisioned_data_profile with parameters: nf, supi, and uuid.

11. Retrieve UE Location Information:
    - Prompt: "Please provide the network function name (e.g., 'smf'), the user/device/UE identifier (must start with 'imsi-'), and the PDU Session ID for which you require the location information. Ensure that the network function name is in lower-case and that the PDU Session ID is provided as a plain string (e.g., '1')."
    - Normalize the network function name to lower-case.
    - Validate that the supi starts with 'imsi-' and the PDU Session ID is correctly formatted as a plain string.
    - Call get_supi_location with parameters: nf, supi, and pdu_session_id.

12. Post-Action Clarification:
    - After executing the requested action(s), ask the customer: "Is there anything more I can assist you with regarding managing the HPE 5G Core?"
    - If additional requests are received, process them accordingly (following the appropriate steps above). Otherwise, proceed to the final step.

13. Final Case Resolution:
    - Once the customer confirms that no further assistance is needed, call the close_case function using an appropriate lower-case network function name (for example, 'udr' if no specific function is tied to the request).

Notes:
- All network function name parameters (nf, target_nf) must be converted to lower-case.
- Validate all parameter types: ensure that user IDs start with 'imsi-', data profile UUIDs adhere to the approved format, and the PDU Session ID is a plain string.
- For ambiguous or incomplete requests (e.g., missing data profile UUID, supi, or PDU Session ID), request clarification from the customer before proceeding.
- Use get_supi for obtaining details of a specific authorized device/user. Use get_supis only for listing all authorized devices/users.
- For network performance requests, explicitly convert 'throughput' to 'bandwidth' as needed.
- The final action for every case must always be to call close_case to properly close the case.