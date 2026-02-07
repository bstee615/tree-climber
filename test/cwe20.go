func(t *testing.T) {
					vrequire := require.New(t)
					accessibleObjectIds := vctx.accessibilitySet.AccessibleObjectIDs(objectRelation.Namespace, objectRelation.Relation, subject)

					
					resolvedObjectIds, err := vctx.tester.Lookup(context.Background(), objectRelation, subject, vctx.revision)
					vrequire.NoError(err)

					sort.Strings(accessibleObjectIds)
					sort.Strings(resolvedObjectIds)

					for _, accessibleObjectID := range accessibleObjectIds {
						vrequire.True(
							contains(resolvedObjectIds, accessibleObjectID),
							"Object `%s` missing in lookup results for %s#%s@%s: Expected: %v. Found: %v",
							accessibleObjectID,
							nsDef.Name,
							relation.Name,
							tuple.StringONR(subject),
							accessibleObjectIds,
							resolvedObjectIds,
						)
					}

					
					for _, resolvedObjectID := range resolvedObjectIds {
						isMember, err := vctx.tester.Check(context.Background(),
							&v0.ObjectAndRelation{
								Namespace: nsDef.Name,
								Relation:  relation.Name,
								ObjectId:  resolvedObjectID,
							},
							subject,
							vctx.revision,
						)
						vrequire.NoError(err)
						vrequire.True(
							isMember,
							"Found Check failure for relation %s:%s#%s and subject %s",
							nsDef.Name,
							resolvedObjectID,
							relation.Name,
							tuple.StringONR(subject),
						)
					}
				}