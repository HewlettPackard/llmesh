Improved Routine Instructions:

1. Identify the type of customer request by parsing the input for keywords corresponding to the following categories:
   a. If the request mentions monitoring network performance (KPIs such as latency, bandwidth, signal strength), then proceed to step 2.
   b. If the request is about retrieving the AMF-NGAP status, then proceed to step 3.
   c. If the request asks for network function logs, then proceed to step 4.
   d. If the request is to read a network function profile, then proceed to step 5.
   e. If the request is about obtaining the list of authorized users/devices/UEs, then proceed to step 6.
   f. If the request is about retrieving information for a specific user/device/UE, then proceed to step 7.
   g. If the request is to retrieve the list of approved data profiles, then proceed to step 8.
   h. If the request is for details of a specific data profile, then proceed to step 9.
   i. If the request is to assign a new data profile to a user, then proceed to step 10.
   j. If the request is to obtain UE location information, then proceed to step 11.
   k. Else, if the request does not match any of the above, politely prompt the customer for clarification and escalate if necessary.

2. Monitor Network Performance:
   a. Prompt the customer: "Please provide the network function name and the specific KPI metric you want to track (e.g., latency, bandwidth, signal strength). Note: Kindly use lower-case for the network function name as expected by the system."
   b. Before calling the function, convert the provided network function name to lower-case if needed.
   c. Then call the get_network_performance function with parameters nf and metric.

3. Retrieve AMF-NGAP Status:
   a. Prompt the customer: "Please provide the network function name where the AMF-NGAP status is required. Please use lower-case, e.g., 'amf'."
   b. Normalize the network function name to lower-case before calling the function.
   c. Then call the get_amf_ngap_status function with parameter nf.

4. Retrieve Logs from a Network Function:
   a. Prompt the customer: "Please specify the network function name from which you require the logs. Please ensure the name is in lower-case (e.g., 'ausf', 'udm')."
   b. Normalize the network function name to lower-case before calling the get_logs function.
   c. Then call the get_logs function with parameter nf.

5. Read Network Function Profile:
   a. Prompt the customer: "Please provide the network function name for which you need the profile. Use lower-case (e.g., 'udm', 'amf', 'smf')."
   b. Normalize the provided network function name to lower-case.
   c. Then call the get_nf_profile function with parameters nf and target_nf (where target_nf is the network function for which profile information is required, in lower-case).

6. Retrieve the List of Authorized Users/Devices/UEs:
   a. Prompt the customer: "Please confirm if you want the list of all authorized devices/users (those with IDs starting with 'imsi-') accessed in the HPE 5G Core."
   b. Then call the get_supis function with parameter nf. Ensure that the network function used (e.g., 'udm') is provided in lower-case.

7. Retrieve Information for a Specific User/Device/UE:
   a. Prompt the customer: "Please provide the identifier for the specific user/device/UE. Ensure that the ID starts with 'imsi-'. If it does not, please re-check the approved device list and provide the correct ID."
   b. Then call the get_supi function with parameters nf and supi. Normalize the network function name to lower-case.

8. Retrieve the List of Authorized Data Profiles:
   a. Prompt the customer: "Please provide the network function name to retrieve the list of authorized data profiles. Ensure the name is in lower-case (e.g., 'udr')."
   b. Normalize the network function name to lower-case before calling the get_dataprofiles function.
   c. Then call the get_dataprofiles function with parameter nf.

9. Retrieve Specific Data Profile Information:
   a. Prompt the customer: "Please provide the UUID of the data profile you want to retrieve."
   b. Then call the get_dataprofile function with parameters nf and uuid. Ensure the network function name (e.g., 'udr') is in lower-case.

10. Assign a New User Data Profile:
   a. Prompt the customer: "Please provide the network function name, the user’s ID (must start with 'imsi-' or match an entry from the approved device list), and the data profile’s UUID (from the approved list). For instance, network function name should be provided in lower-case."
   b. If the user’s identifier does not start with 'imsi-', ask: "Can you confirm the identifier or provide additional details to locate the device in the approved list?"
   c. If the specified data profile does not exist in the approved data profiles list, ask: "The provided data profile UUID is not recognized. Can you please verify or provide additional details?"
   d. Once all required information is verified and normalized (especially ensuring network function name is lower-case), then call the patch_provisioned_data_profile function with parameters nf, supi, and uuid.

11. Retrieve UE Location Information:
   a. Prompt the customer: "Please provide the network function name, the user/device/UE ID (must start with 'imsi-'), and the PDU Session ID for which you require the location information. Ensure the network function name is in lower-case (e.g., 'smf') and that the PDU Session ID is provided as a plain string without decimals if not applicable."
   b. Normalize the network function name to lower-case.
   c. Then call the get_supi_location function with parameters nf, supi, and pdu_session_id.

12. After completing the requested action(s), always ask the customer:
   "Is there anything more I can assist you with regarding managing the HPE 5G Core?"

13. Final Case Resolution:
   a. Once the customer confirms that no further assistance is needed, call the close_case function with a network function parameter. Use a suitable network function name in lower-case as applicable (e.g., if no specific function, use the core management function identifier, such as 'udr' or similar).

Note: In all function calls, ensure that the network function names (nf, target_nf) are normalized and passed in lower-case to comply with the expected inputs. This extra validation helps avoid errors due to capitalization mismatches.

Final action for resolution: call the close_case function as the last step.