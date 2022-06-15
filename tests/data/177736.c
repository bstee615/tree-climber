 static int samldb_check_user_account_control_acl(struct samldb_ctx *ac,
 						 struct dom_sid *sid,
 						 uint32_t user_account_control,
 						 uint32_t user_account_control_old)
 {
 	int i, ret = 0;
 	bool need_acl_check = false;
 	struct ldb_result *res;
 	const char * const sd_attrs[] = {"ntSecurityDescriptor", NULL};
         struct security_token *user_token;
         struct security_descriptor *domain_sd;
         struct ldb_dn *domain_dn = ldb_get_default_basedn(ldb_module_get_ctx(ac->module));
       struct ldb_context *ldb = ldb_module_get_ctx(ac->module);
         const struct uac_to_guid {
                 uint32_t uac;
               uint32_t priv_to_change_from;
                 const char *oid;
                 const char *guid;
                 enum sec_privilege privilege;
                 bool delete_is_privileged;
               bool admin_required;
                 const char *error_string;
         } map[] = {
                 {
 		},
 		{
 			.uac = UF_DONT_EXPIRE_PASSWD,
 			.guid = GUID_DRS_UNEXPIRE_PASSWORD,
 			.error_string = "Adding the UF_DONT_EXPIRE_PASSWD bit in userAccountControl requires the Unexpire-Password right that was not given on the Domain object"
 		},
 		{
 			.uac = UF_ENCRYPTED_TEXT_PASSWORD_ALLOWED,
 			.guid = GUID_DRS_ENABLE_PER_USER_REVERSIBLY_ENCRYPTED_PASSWORD,
 			.error_string = "Adding the UF_ENCRYPTED_TEXT_PASSWORD_ALLOWED bit in userAccountControl requires the Enable-Per-User-Reversibly-Encrypted-Password right that was not given on the Domain object"
 		},
 		{
 			.uac = UF_SERVER_TRUST_ACCOUNT,
 			.guid = GUID_DRS_DS_INSTALL_REPLICA,
 			.error_string = "Adding the UF_SERVER_TRUST_ACCOUNT bit in userAccountControl requires the DS-Install-Replica right that was not given on the Domain object"
 		},
 		{
 			.uac = UF_PARTIAL_SECRETS_ACCOUNT,
 			.guid = GUID_DRS_DS_INSTALL_REPLICA,
 			.error_string = "Adding the UF_PARTIAL_SECRETS_ACCOUNT bit in userAccountControl requires the DS-Install-Replica right that was not given on the Domain object"
 		},
                         .guid = GUID_DRS_DS_INSTALL_REPLICA,
                         .error_string = "Adding the UF_PARTIAL_SECRETS_ACCOUNT bit in userAccountControl requires the DS-Install-Replica right that was not given on the Domain object"
                 },
               {
                       .uac = UF_WORKSTATION_TRUST_ACCOUNT,
                       .priv_to_change_from = UF_NORMAL_ACCOUNT,
                       .error_string = "Swapping UF_NORMAL_ACCOUNT to UF_WORKSTATION_TRUST_ACCOUNT requires the user to be a member of the domain admins group"
               },
               {
                       .uac = UF_NORMAL_ACCOUNT,
                       .priv_to_change_from = UF_WORKSTATION_TRUST_ACCOUNT,
                       .error_string = "Swapping UF_WORKSTATION_TRUST_ACCOUNT to UF_NORMAL_ACCOUNT requires the user to be a member of the domain admins group"
               },
                 {
                         .uac = UF_INTERDOMAIN_TRUST_ACCOUNT,
                         .oid = DSDB_CONTROL_PERMIT_INTERDOMAIN_TRUST_UAC_OID,
 			.error_string = "Updating the UF_TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION bit in userAccountControl is not permitted without the SeEnableDelegationPrivilege"
 		}
 
 	};