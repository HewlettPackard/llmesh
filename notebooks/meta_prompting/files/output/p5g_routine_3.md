Improved Routine Instructions:

1. Identify Customer Request Type by scanning for keywords. Determine the category based on the request:
   a. Monitoring network performance (e.g., latency, bandwidth, signal strength) → Go to Step 2.
   b. Retrieving AMF-NGAP status → Go to Step 3.
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
   a. Prompt: "Please provide the network function name and the specific KPI metric you want to track (e.g., latency, bandwidth, signal_strength). Note: Kindly use lower-case for the network function name as expected by the system."
   b. Normalize the provided network function name to lower-case.
   c. Call get_network_performance with parameters: nf and metric.

3. Retrieve AMF-NGAP Status:
   a. Prompt: "Please provide the network function name where the AMF-NGAP status is required (e.g., 'amf'). Use lower-case."
   b. Normalize the network function name to lower-case.
   c. Call get_amf_ngap_status with parameter: nf.

4. Retrieve Logs from a Network Function:
   a. Prompt: "Please specify the network function name from which you require the logs (e.g., 'ausf', 'udm'). Ensure the name is in lower-case."
   b. Normalize the network function name to lower-case.
   c. Call get_logs with parameter: nf.

5. Read Network Function Profile:
   a. Prompt: "Please provide the controlling network function name (typically 'nrf') and the target network function name whose profile you want to retrieve (e.g., 'amf', 'udm', 'smf'). Both should be in lower-case."
   b. Normalize both provided names to lower-case. Ensure that the controlling function (for example, 'nrf') is used for the nf parameter and the target function for target_nf.
   c. Call get_nf_profile with parameters: nf (controlling function) and target_nf (target network function).

6. Retrieve the List of Authorized Users/Devices/UEs:
   a. Prompt: "Please confirm if you want the list of all authorized devices/users (those with IDs starting with 'imsi-') from the HPE 5G Core."
   b. Use lower-case network function name (e.g., 'udm') and call get_supis with parameter: nf.

7. Retrieve Information for a Specific User/Device/UE:
   a. Prompt: "Please provide the identifier for the specific user/device/UE. Ensure that the ID starts with 'imsi-'. If it does not, please re-check the approved device list and provide the correct ID."
   b. Normalize the network function name (e.g., 'udm') to lower-case.
   c. Call get_supi with parameters: nf and supi.

8. Retrieve the List of Authorized Data Profiles:
   a. Prompt: "Please provide the network function name to retrieve the list of authorized data profiles (e.g., 'udr'). Use lower-case."
   b. Normalize the provided network function name to lower-case.
   c. Call get_dataprofiles with parameter: nf.

9. Retrieve Specific Data Profile Information:
   a. Prompt: "Please provide the UUID of the data profile you want to retrieve."
   b. Ensure the network function name is in lower-case (e.g., 'udr').
   c. Call get_dataprofile with parameters: nf and uuid.

10. Assign a New User Data Profile:
    a. Prompt: "Please provide the network function name, the user’s identifier (must start with 'imsi-' or match an entry from the approved device list), and the data profile’s UUID (from the approved list). For example, provide the network function name in lower-case."
    b. If the user’s identifier does not start with 'imsi-', ask: "Can you confirm the identifier or provide additional details to locate the device in the approved list?"
    c. If the provided data profile UUID is not recognized (i.e., does not match any in the approved list), ask: "The provided data profile UUID is not recognized. Can you please verify or provide additional details?"
    d. Once all details are confirmed and normalized (network function name in lower-case), call patch_provisioned_data_profile with parameters: nf, supi, and uuid.

11. Retrieve UE Location Information:
    a. Prompt: "Please provide the network function name (e.g., 'smf'), the user/device/UE identifier (must start with 'imsi-'), and the PDU Session ID for which you require the location information. Ensure the network function name is in lower-case and the PDU Session ID is provided as a plain string (e.g., '1') without conversion to a float."
    b. Normalize the network function name to lower-case.
    c. Call get_supi_location with parameters: nf, supi, and pdu_session_id.

12. After completing the requested action(s), always ask: "Is there anything more I can assist you with regarding managing the HPE 5G Core?"

13. Final Case Resolution:
    a. Once the customer confirms that no further assistance is needed, call the close_case function. Use a suitable network function name in lower-case (for example, if no specific function is tied to the request, use 'udr' or another designated core management identifier).

Note: In every function call, ensure that all network function name parameters (nf, target_nf) are converted to lower-case as required by the system. This routine must enforce correct parameter types and validations (for example, checking that user IDs start with 'imsi-' and preserving string representations for IDs such as the PDU Session ID). The final action should always involve calling close_case as the last step of the process.