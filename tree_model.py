# D. Gibson, 2009
#
##################################################################
# Client Home Models
##################################################################

##################################################################
# Configuration treeview Models
##################################################################
# The tree structure would link in various kinds of objects like TimeOfYear, DaysOfWeek, etc.
# The Django View would navigate the tree structure to send the html to render on the Browser.
ATTRIB_TYPE = (
	(0, 'TimeOfYear'),
	(1, 'DaysOfWeek'),
	(2, 'HoursOfDay'),
	(3, 'TimeOfYearHeader'),  # For TimeOfYear header.
	(4, 'SpecialDates'),  # For Special Dates that can add HoursOfDay.
	(5, 'SpecialDatesHeader'),  # For Special Dates header that can add Special Dates.
	(6, 'SpecificYearlyDate'),   # For Specific Yearly Date that can add HoursOfDay.
	(7, 'SpecificYearlyDatesHeader')   # For Specific Yearly Date Header that can add SpecificDate.
	)
# The tuple below is only required for when a user clicks the Add . . . button in the tree.
# The tuple identifies what kind of object to link to the new objects Add . . .  button in the tree.
# For existing objects, each object knows what kind of child object it can add based on the database, but somehow the database
# has to get populated when the object is first created, and this is how I currently do it.
# There is a one-to-one mapping between the indexes of ATTRIB_TYPE and ATTRIB_TYPE_TO_ENTITY.
ATTRIB_TYPE_TO_ENTITY = (
	(0, 'TimeOfYear', None),
	(1, 'DaysOfWeek', None),
	(2, 'HoursOfDay', None),
	(3, 'TextString', 0),  # For TimeOfYear header.
	(4, 'SpecialDate', 2),  # For Special Dates that can add HoursOfDay.
	(5, 'TextString', 4),  # For Special Dates header that can add Special Dates.
	(6, 'SpecificDate', 2),   # For Specific Yearly Date that can add HoursOfDay.
	(7, 'TextString', 6)   # For Specific Yearly Date Header that can add SpecificDate.
	)

newform_header = '<li id="10000"><span class="folder"><fieldset style="width:300px;"><form id="addtreeform" class="addtreeform" enctype="multipart/form-data" method="post" action="{{ my_url }}configtree/{{ state }}/?leaf_type= addleaf_{{ leaf_type }}&parent={{ parent }}" style="padding: 0 0 0 0px; margin: 0 0 0 0px;">'
newform_footer = '<div class="submit-row"><input type="submit" name = "submitbutton" value="Cancel"/><input type="submit"  name = "submitbutton" value="Save"/></div></form><div id="add_output"></div></fieldset></span></li>'
newform_header_old = '<form id="edittreeform" class="edittreeform" enctype="multipart/form-data" method="post" action="/bookitnow/configtree/{{ state }}/{{  sp_key }}/?leaf_type= {{ leaf_type }}" style="padding: 0 0 0 0px; margin: 0 0 0 0px;">'
form_header = '<form id="edittreeform" class="edittreeform" enctype="multipart/form-data" method="post" action="{{ my_url }}configtree/{{ state }}/?editleaf= {{ leaf_id }}" style="padding: 0 0 0 0px; margin: 0 0 0 0px;">'
form_footer = '<div class="submit-row"><input type="submit" name = "submitbutton" value="Cancel"/><input type="submit" name = "submitbutton" value="Save"/></div></form><div id="gotooutput"></div>'


class EntityType(models.Model):
	def __str__(self):
		return self.name

	name = models.CharField(max_length=30)

	class Admin:
		pass

class EntityToAvailKey(models.Model):
	def __str__(self):
		return '%s' % (self.entity_type)
	
	# just use default id for avail_key
	#avail_key = models.IntegerField(primary_key = True)
	sp_key = models.IntegerField(null=True, blank=True)
	locn_key = models.IntegerField(null=True, blank=True)
	service_key = models.IntegerField(null=True, blank=True)
	resource_key = models.IntegerField(null=True, blank=True)
	#entity_type = models.IntegerField()
	entity_type = models.ForeignKey(EntityType)
	effective_date = models.DateField()
	base = models.BooleanField()
	inherited = models.BooleanField()
	updated_date = models.DateTimeField()
	processed = models.DateTimeField(null=True, blank=True)
	
	def delete_profile(cls, avail_id):
		"""
		This deletes a profile out of this class, by:
		1.  Calling the backend stored proc 'f_gui_to_model(avail_id, False, True) to delete the backend profile.
		2.  Checking if the avail_object still exists and if it does . . .
		3.  and if it does, delete ConfigTree and avail_object.
		"""
		print 'In delete_profile with avail_id: %s' % (avail_id)
		avail_object = cls.objects.get(id = avail_id)
		if avail_object.processed is None: # Has not been processed, so just delete gui objects.
			TreeStructure.delete_tree(avail_object.id)
			avail_object.delete()
			return_info = {'errors': False, 'error_html': None}
			return return_info
		print 'In delete_profile, got past stand-alone tree'

		param_list = ["avail_id", "check_only", "process_tp" ]
		stored_proc = StoredProcException("f_gui_to_model", param_list)
		sql_dict = {}
		sql_dict['avail_id'] = avail_id
		sql_dict['check_only'] = False
		sql_dict['process_tp'] = 'D'  # For deleting a profile.

		myresult = stored_proc.alchModify(sql_dict)
		if len(myresult) == 0:  # Check if nothing returned, means successful
			print 'result set for f_gui_to_model is empty indicating success'
			return_info = {'errors': False, 'error_html': None}
                        # Need to delete gui objects at this time (if backend has not already done so, because backend delete was sucessful.
                        avail_objects = cls.objects.filter(id=avail_id)
                        if len(avail_objects) > 0:
                                TreeStructure.delete_tree(avail_objects[0].id) # Assume Config tree exists, and needs to be deleted
                                avail_objects[0].delete()
		else:
			print 'result set for f_gui_to_model is indicating errors'
			return_info = {'errors': True, 'error_html': '<span>%s</span>' % (myresult)}
		return return_info

	delete_profile = classmethod(delete_profile)

	def copy(self, sp_key=None, locn_key=None, service_key=None, resource_key=None, entity_type_id=None):
		"""
		Creates a new object based on this object, but can over-ride passed in locn_key, or
		service_key, or resource_key, or identity_type_id parameters.
		"""
		if self.inherited:
			return False
		params = dict(self.__dict__)
		del params['id']
		oneday = datetime.timedelta(days=1)
		params['effective_date'] = datetime.date.today() + oneday
		params['updated_date'] = datetime.datetime.now()
		#params['updated_date'] = datetime.date.today()
		params['base'] = False
		if sp_key is not None:
			params['sp_key'] = sp_key
		if locn_key is not None:
			params['locn_key'] = locn_key
		if service_key is not None:
			params['service_key'] = service_key
		if resource_key is not None:
			params['resource_key'] = resource_key
		if entity_type_id is not None:
			params['entity_type_id'] = entity_type_id
		print params
		new_avail = self.__class__(**params)
		# Added July 9, 2009 to solve numerous problems.
		new_avail.processed = None # Set timestamp to null.
		new_avail.save()
		return new_avail.id # return new avail_key for config tree.
	
	def process(self,check=False, delete=False):
		if delete:
			process = 'D' # for deleting a profile
		else:
			process = ' ' # Blank or null for process.
			
		param_list = ["avail_id", "check_only", "process_tp" ]
		stored_proc = StoredProcException("f_gui_to_model", param_list)
		sql_dict = {}
		sql_dict['avail_id'] = self.id
		sql_dict['check_only'] = check
		sql_dict['process_tp'] = process  

		myresult = stored_proc.alchModify(sql_dict)
		if len(myresult) == 0:  # Check if nothing returned, means successful
			print 'result set for f_gui_to_model is empty'
			return_info = {'errors': False, 'error_html': None}
		else:
			print 'result set for f_gui_to_model indicates errors'
			return_info = {'errors': True, 'error_html': '<span>%s</span>' % (myresult)}
		return return_info

	def change_effective_date(self, effective_date):
		print 'In change_effective_date'
		old_effective_date = self.effective_date # Remember old date in case stored proc fails.
		self.effective_date = effective_date
		self.save() # Store the new effective date so the stored proc can pick it up.
		process = 'E' # Change to effective_data only.
		check = False
		
		param_list = ["avail_id", "check_only", "process_tp" ]
		stored_proc = StoredProcException("f_gui_to_model", param_list)
		sql_dict = {}
		sql_dict['avail_id'] = self.id
		sql_dict['check_only'] = check
		sql_dict['process_tp'] = process  

		myresult = stored_proc.alchModify(sql_dict)
		if len(myresult) == 0:  # Check if nothing returned, means successful
			print 'result set for f_gui_to_model is empty'
			return_info = {'errors': False, 'error_html': None}
		else:
			print 'result set for f_gui_to_model indicates errors'
                        self.effective_date = old_effective_date # restore old effective date.
                        self.save()
			return_info = {'errors': True, 'error_html': '<span>%s</span>' % (myresult)}
		return return_info
	
	class Admin:
		pass

class TreeStructure(models.Model):
	def __str__(self):
		# return 'Id: %s, Type: %s Attribute Type: %s Attribute Reference: %s' % (self.owner_id,
		return 'Avail_key: %i, Attribute Type: %s, Attribute Reference: %i' % (int(self.avail_key),
					     #EntityType.objects.filter(id__exact=self.owner_type_id)[0],
					     ATTRIB_TYPE[int(self.attribute_type)][1],
					     self.attribute_ref)

	def compare_tree(cls, avail_key, new_avail_key, treestruct_id=None, new_treestruct_id=None, results=[ ]):
		"""
		Compares two configtrees, Returns False if error, True if identical, and a dictionary
		if differences.  This is a literal compare intended to verify a copied tree.
		"""
		if (avail_key and new_avail_key) is None:
			return False # if either key is None, abort.
		
		if treestruct_id is None:
			node_set = cls.objects.filter(avail_key__exact = avail_key).filter(parent__isnull = True)
			new_node_set = cls.objects.filter(avail_key__exact = new_avail_key).filter(parent__isnull = True)
		else:
			node_set = cls.objects.filter(avail_key__exact = avail_key).filter(parent__exact = treestruct_id)
			new_node_set = cls.objects.filter(avail_key__exact = new_avail_key).filter(parent__exact = new_treestruct_id)
		if len(node_set) != len(new_node_set):
			results.append({'avail_key': avail_key, 'new_avail_key': new_avail_key, 'treestruct_id': treestruct_id, 'newtreestruct_id': new_treestruct_id, 'sizediff': len(new_node_set) - len(node_set)})
			#rint results
			return results # will have to handle this from recursion point of view.
		if (len(node_set) == 0) or (len(new_node_set) == 0):
			return  results # ends final recursion loop, final success, no more children to process.
		else:
			found = False
			for node in node_set:
				#print 'node type: %s, node ref: %s' % (node.get_attribute_type_display(),node.attribute_ref)		
				node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[int(node.attribute_type)][1], node.attribute_ref))
				for new_node in new_node_set:
					#print 'new node type: %s, new node ref: %s' % (new_node.get_attribute_type_display(),new_node.attribute_ref)
					#(identical, result) = node_object.compare(new_node.id)
					if node.editable != new_node.editable:
						continue # if not right node to compare, break out and get next node.
					if node.attribute_type != new_node.attribute_type:
						continue # if not right node to compare, break out and get next node.
					#print 'new node type: %s, new node ref: %s' % (new_node.get_attribute_type_display(),new_node.attribute_ref)
					#found = True
					(identical, result) = node.compare(new_node.id)
					if identical: # we now want to go down the tree some more
						#print 'Found identical!!'
						found = True
						results = cls.compare_tree(avail_key, new_avail_key, node.id, new_node.id, results) # recursively call self.
						break
					#else:  # not identical, need to propogate errors up.
						#print 'NOT identical!!'
						#results += result
				if not found:
					results.append({ 'object': result[-1]['object'], 'node_id': node.id, 'status': 'node not found' })
					return results
				
		return results # Ends each recursion call loop.
	
	compare_tree = classmethod(compare_tree)

	def delete_tree(cls, avail_key, treestruct_id=None, nodeid_xref={ }):
		"""
		Deletes a configtree for avail_key.
		"""
		if treestruct_id is None:
			node_set = cls.objects.filter(avail_key__exact = avail_key).filter(parent__isnull = True)
		else:
			node_set = cls.objects.filter(avail_key__exact = avail_key).filter(parent__exact = treestruct_id)
		if len(node_set) == 0:
			return None # ends all recursion, if no leaves left.
		else:
			for node in node_set:
				# Three lines below are already done in TreeStructure method delete_node()
				#print 'node type: %s, node ref: %s' % (node.get_attribute_type_display(),node.attribute_ref)
				#node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[int(node.attribute_type)][1], node.attribute_ref))
				#node_object.delete()
				node.delete_node()  # This will delete this node and all its children.

	delete_tree = classmethod(delete_tree)
	
	def copy_tree(cls, avail_key, new_avail_key, treestruct_id=None, nodeid_xref={ }):
		"""
		Gets all the html for the nodes for a particular avail_key and with a parent of treestruct_id.
		"""
		if (avail_key and new_avail_key) is None:
			return False # if either key is None, abort.
		
		if treestruct_id is None:
			node_set = cls.objects.filter(avail_key__exact = avail_key).filter(parent__isnull = True)
		else:
			node_set = cls.objects.filter(avail_key__exact = avail_key).filter(parent__exact = treestruct_id)
		if len(node_set) == 0:
			return  nodeid_xref # ends final recursion loop, final success, no more children to process.
		else:
			#nodeid_xref = { }
			for node in node_set:
				print 'node type: %s, node ref: %s' % (node.get_attribute_type_display(),node.attribute_ref)
				nodeid_xref[node.id] = None #save original node id
				#node_object = eval('%s.objects.get(id=%i)' % (node.get_attribute_type_display(), node.attribute_ref))
				node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[int(node.attribute_type)][1], node.attribute_ref))
				node_object_id = node_object.copy()
				print node_object_id
				dict_params = dict(node.__dict__)
				del dict_params['id'] # remove id, because we want to do an insert
				print dict_params
				dict_params['avail_key'] = new_avail_key
				dict_params['attribute_ref'] = node_object_id
				if node.parent is not None:
					dict_params['parent'] = nodeid_xref[node.parent] # To get new parent for new tree.
				print dict_params
				new_node = cls(**dict_params)
				new_node.save()
				print new_node.id
				nodeid_xref[node.id] = new_node.id
				print 'nodeid_xref updated:'
				print nodeid_xref
				nodeid_xref = cls.copy_tree(avail_key, new_avail_key, node.id, nodeid_xref) # recursively call self.

		return nodeid_xref # Ends each recursion call loop.

	copy_tree = classmethod(copy_tree)

	def get_nodes(cls, avail_key, treestruct_id=None):
		"""
		Gets all the html for the nodes for a particular avail_key and with a parent of treestruct_id.
		"""
		if treestruct_id is None:
			node_set = cls.objects.filter(avail_key__exact = avail_key).filter(parent__isnull = True)
		else:
			node_set = cls.objects.filter(avail_key__exact = avail_key).filter(parent__exact = treestruct_id)
		if len(node_set) == 0:
			return '[]'
		else:
			tree_list = [ ]
			for node in node_set:
				print 'node type: %s, node ref: %s' % (node.get_attribute_type_display(),node.attribute_ref)
				#node_object = eval('%s.objects.get(id=%i)' % (node.get_attribute_type_display(), node.attribute_ref))
				node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[int(node.attribute_type)][1], node.attribute_ref))
				tree_list.append(node_object.get_html(node.id))

		return cjson.encode(tree_list)

	get_nodes = classmethod(get_nodes)
	
	avail_key = models.IntegerField()
	#owner_id = models.IntegerField()
	#owner_type = models.ForeignKey(EntityType)
	parent = models.IntegerField(null=True, blank=True)
	editable = models.BooleanField()
	attribute_type = models.IntegerField(choices=ATTRIB_TYPE)
	attribute_ref = models.IntegerField()

	class Meta:
		ordering = ['id']
		
	def compare(self, node_id):
		"""
		Compares this node with the node_id passed in.
		"""
		result = [ ]
		other_object = self.__class__.objects.get(id = node_id)
		#params = dict(self._dict_)
		#other_params = dict(other_object._dict_)
		identical = False
		found = False
		if self.editable != other_object.editable:
			result.append({'status':'editable conflict' })
			return (identical, result)
		if self.attribute_type != other_object.attribute_type:
			result.append({'status':'type conflict' })
			return (identical, result)
		#rint 'node type: %s, node ref: %s' % (self.get_attribute_type_display(), self.attribute_ref)		
		node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[int(self.attribute_type)][1], self.attribute_ref))
		#rint 'other node type: %s, node ref: %s' % (other_object.get_attribute_type_display(), other_object.attribute_ref)
		other_node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[int(other_object.attribute_type)][1], other_object.attribute_ref))
		(identical, result) = node_object.compare(other_node_object)
		return (identical, result)
		
	def delete_node(self):
		"""
		This will delete a node and all its branches (recursively).
		"""
		print 'In delete_node'
		# Before deleting the object that a node points to, we should check that the object is not referred to
		# by another node - this should seldom be the case, but is possible, particularly for standard TextStrings.
		# We don't want to delete the object if it is used elsewhere - nor its children if the are used elsewhere.
		other_leaves = self.__class__.objects.filter(attribute_type = self.attribute_type).filter(attribute_ref = self.attribute_ref)
		if len(other_leaves) > 1:
			deleteObject_flg = False # Object is referred to more than once.
		else:
			deleteObject_flg = True  # Can delete object
		branches = self.__class__.objects.filter(avail_key = self.avail_key).filter(parent = self.id)
		print 'past getting branches'
		for node in branches:
			node.delete_node() # call this function recursively.
		print '%s.objects.get(id=%i)' % (self.get_attribute_type_display(), self.attribute_ref)
		if deleteObject_flg:
			this_node = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[self.attribute_type][1], self.attribute_ref))
			print this_node
			this_node.delete() # basic model record (object) delete.
		self.delete() # delete this object

	def get_leaf_html(self):
		"""
		Gets leaf html for the object for this record.
		"""
		print 'in TreeStructure get_leaf_html'
		print '%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[self.attribute_type][1], self.attribute_ref)
		#self.node_object = eval('%s.objects.get(id=%i)' % (self.get_attribute_type_display(), self.attribute_ref))
		self.node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[self.attribute_type][1], self.attribute_ref))
		return self.node_object.get_leaf_html(self.id)

	def get_html(self):
		"""
		Gets html for the object for this record.
		"""
		#self.node_object = eval('%s.objects.get(id=%i)' % (self.get_attribute_type_display(), self.attribute_ref))
		self.node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[self.attribute_type][1], self.attribute_ref))
		return self.node_object.get_html(self.id)

	def get_newform_html(cls, newleaf_type):
		print 'In get_newform_html'
		form_call = '%s.get_newform_html()' % (ATTRIB_TYPE_TO_ENTITY[newleaf_type][1])
		print form_call
		form_html = eval('%s.get_newform_html()' % (ATTRIB_TYPE_TO_ENTITY[newleaf_type][1]))
		#print form_html
		return form_html

	get_newform_html = classmethod(get_newform_html)

	def save_newform_data(cls, newleaf_type, parent, avail_key, thisPOST):
		print 'In save_newform_data'
		print 'in TreeStructure save_newform_data'
		print '%s.save_newform_data(%s, %s)' % (ATTRIB_TYPE_TO_ENTITY[newleaf_type][1], 'thisPOST', ATTRIB_TYPE_TO_ENTITY[newleaf_type][2])
		#TimeOfYear.save_newform_data(thisPOST)
		#newrec = eval('%s.save_newform_data(%s, %s)' % (ATTRIB_TYPE_TO_ENTITY[newleaf_type][1], 'thisPOST', ATTRIB_TYPE_TO_ENTITY[newleaf_type][2]))
		new_dict = eval('%s.save_newform_data(%s, %s)' % (ATTRIB_TYPE_TO_ENTITY[newleaf_type][1], 'thisPOST', ATTRIB_TYPE_TO_ENTITY[newleaf_type][2]))
		# Need to add this new record into the right part of the TreeStructure.
		if new_dict['new_rec'] > 0:
		    newtreenode = cls(avail_key = avail_key,
				  parent = parent,
				  editable = True,
				  attribute_type = newleaf_type,
				  attribute_ref = new_dict['new_rec'].id
				  )
		    newtreenode.save()
		    entity_to_avail =  EntityToAvailKey.objects.get(id = avail_key)
		    entity_to_avail.updated_date = datetime.datetime.now()
		    #entity_to_avail.updated_date = datetime.date.today()
		    entity_to_avail.save()
		return new_dict

	save_newform_data = classmethod(save_newform_data)

	def get_form_html(self):
		"""
		Gets form html for the object for this record.
		"""
		print 'In get_form_html, attribute type: %s, attribute ref: %s' % (self.get_attribute_type_display(),
										   self.attribute_ref)
		#self.node_object = eval('%s.objects.get(id=%i)' % (self.get_attribute_type_display(), self.attribute_ref))
		self.node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[self.attribute_type][1], self.attribute_ref))
		#return node_object
		return self.node_object.get_form_html(self.id)

	def save_form_data(self,thisPOST):
		"""
		Gets form html for the object for this record.
		"""
		#node_object = eval('%s.objects.get(id=%i)' % (self.get_attribute_type_display(), self.attribute_ref))
		#return node_object
		print 'in TreeStructure save_form_data'
		#self.node_object = eval('%s.objects.get(id=%i)' % (self.get_attribute_type_display(), self.attribute_ref))
		self.node_object = eval('%s.objects.get(id=%i)' % (ATTRIB_TYPE_TO_ENTITY[self.attribute_type][1], self.attribute_ref))
		response = self.node_object.save_form_data(thisPOST)
		#return node_object.get_form_html(self.id)
		entity_to_avail =  EntityToAvailKey.objects.get(id = self.avail_key)
		entity_to_avail.updated_date = datetime.datetime.now()
		#entity_to_avail.updated_date = datetime.date.today()
		entity_to_avail.save()
		return response
	
	
	class Admin:
		pass

# Generic functions for use in all objects below (until abstract classes are working).
def generic_copy(self):
	dict_params = dict(self.__dict__) # make a copy of parameters
	del dict_params['id'] # remove id, because we want to do an insert
	new_node = self.__class__(**dict_params)
	new_node.save()
	print new_node.id
	return new_node.id

def generic_compare(self, node_object):
	"""
	Compares this node with the node_id passed in.
	"""
	#print 'comparing:'
	#print self
	#print node_object
	result = [ ]
	#other_object = self.__class_.objects.get(id = node_id)
	params = dict(self.__dict__)
	del params['id']
	other_params = dict(node_object.__dict__)
	del other_params['id']
	identical = False
	difference = False
	found = False
	for param in params:
		for other_param in other_params:
			try:  # put in this, in case non-comparable types.
				if param == other_param:
					found = True
					if self.__dict__[param] == node_object.__dict__[other_param]: # compare contents
						#print 'in identical check'
						#print self.__dict__[param]
						#print node_object.__dict__[other_param]
						pass
					else: # not equal
						difference = True
						# To verbose for humans
						#result.append({'object': self.__str__(), param : self.__dict__[param], 'other_object': node_object.__str__(), 'other_' + other_param: node_object.__dict__[other_param], 'status': 'notequal' })
					break # if we found two parameters to compare, then get next param.
			except:
				result.append({param : self.__dict__[param], 'other_' + other_param: node_object.__dict__[other_param], 'status': 'different type' })
	if not found:
		#result.append({param : self.__dict__[param], 'status': 'not found' })
		result.append({'object': self.__str__(), 'other_object': node_object.__str__(), 'status': 'parameter not found' })
		return (identical, result)
	if difference:
		result.append({'object': self.__str__(), 'other_object': node_object.__str__(), 'status': 'difference found'})
	else:
		identical = True
	return (identical, result)
	
class SpecificDate(models.Model):
	MONTHS_OF_YEAR = (
		(1, 'January'),
		(2, 'February'),
		(3, 'March'),
		(4, 'April'),
		(5, 'May'),
		(6, 'June'),
		(7, 'July'),
		(8, 'August'),
		(9, 'September'),
		(10, 'October'),
		(11, 'November'),
		(12, 'December')
		)

	month = models.IntegerField(choices=MONTHS_OF_YEAR)
	day = models.IntegerField()
	closed = models.BooleanField()
	user_add_child = models.BooleanField(editable=False)
	child_type = models.IntegerField(choices=ATTRIB_TYPE, editable=False)

	def __str__(self):
		return 'Id: %i, %s %i' % (self.id,
					     self.MONTHS_OF_YEAR[int(self.month) - 1][1], self.day)
	def compare(self, node_object):
		print 'In SpecificDate, compare method'
		return generic_compare(self, node_object)

	def copy(self):
		print 'In SpecificDate, copy method'
		return generic_copy(self)

	def get_leaf_render(self, treestruct_id):
		#print 'In SpecificDate, get_leaf_render() '
		render = '%s %i %s' % (self.MONTHS_OF_YEAR[self.month - 1][1], self.day, self.closed and 'CLOSED' or ' ')
		if self.user_add_child:
			# Modified so that span has an id containing the treestruct_id, and button has and id containing the type of leaf.
			text = '<span id="%i" class="leaf">%s</span> <button name="Add %s" id="addleaf_%i" class="leafbutton">Add %s</button></button><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, render, self.get_child_type_display(), self.child_type, self.get_child_type_display(), treestruct_id)
		else:
			text = '<span id="%i" class="leaf">%s</span></button><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, render, treestruct_id)

		return text

	def get_leaf_html(self, treestruct_id):
		return self.get_leaf_render(treestruct_id)
		
	def get_html(self, treestruct_id):
		#print 'In TimeOfYear get_html() '
		render = self.get_leaf_render(treestruct_id)
		#print render
		text = '<fieldset style="width:400px;">' + render + '</fieldset>'
		if self.user_add_child:
			node = {'text': text, 'id': str(treestruct_id), 'classes':'folder', 'hasChildren': 'true'}  # id is used to refer to node later.
		else:
			node = {'text': text, 'id': str(treestruct_id), 'classes':'folder'}  # id is used to refer to node later.
		return node

	def get_newform_html(cls):
		print 'In TreeObject get_newform_html'
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		#ThisForm = ModelForm(cls) # Django 1.0
		thisform = ThisForm()
		text = newform_header + thisform.as_p() + newform_footer
		return text
	get_newform_html = classmethod(get_newform_html)


	def save_newform_data(cls, thePOST, add_leaf=2):
		print 'In save_newform_data'
		print 'in SpecificDate save_form_data'
		if add_leaf is None:
			add_leaf = 2 # default
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm(thePOST)
		print 'After form creation'
		if thisform.is_valid():
			print 'POST data valid'
			thisform.full_clean()
			record = thisform.save(commit=False)
			print 'Past form save to temp record'
			new_rec = cls(month = int(record.month),
				      day = int(record.day),
				      closed = record.closed,
				      user_add_child = not record.closed,
				      child_type = int(add_leaf)
				      )
			print 'Past creating new_rec'
			new_rec.save()
			#return new_rec
			errors = False
			text = 'Record Saved'
			print 'Record Saved'
		else: # form not valid.
			new_rec = -100
			errors = True
			print 'POST data invalid'
			text = newform_header + thisform.as_p() + newform_footer
			#print text
		return_data = {'html': text, 'errors': errors, 'new_rec': new_rec}
		return return_data

	save_newform_data = classmethod(save_newform_data)

	def get_form_html(self, treestruct_id):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		thisform = ThisForm(self.__dict__)
		text = form_header + thisform.as_p() + form_footer
		#node = {'text': text, 'id': str(treestruct_id)}  # id is used to refer to node later.
		return text
	
	def save_form_data(self, thePOST):
		print 'In save_form_data'
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		thisform = ThisForm(thePOST)
		print 'After form creation'
		if thisform.is_valid():
			print 'POST data valid'
			thisform.full_clean()
			record = thisform.save(commit=False)
			self.month = record.month
			self.day = record.day
			self.closed = record.closed
			self.user_add_child = not record.closed
			self.save()
			html = '<h1 style="color:red;">Record Saved</h1>'
			return {'html': html, 'errors': False}
			#return '<h1 style="color:red;">Record Saved</h1>'
		else:
			print 'POST data invalid'
			text = form_header + thisform.as_p() + form_footer
			#print text
			return {'html': text, 'errors': True}
	
class TimeOfYear(models.Model):
	MONTHS_OF_YEAR = (
		(1, 'January'),
		(2, 'February'),
		(3, 'March'),
		(4, 'April'),
		(5, 'May'),
		(6, 'June'),
		(7, 'July'),
		(8, 'August'),
		(9, 'September'),
		(10, 'October'),
		(11, 'November'),
		(12, 'December')
		)

	def __str__(self):
		# return 'Id: %s, Type: %s Attribute Type: %s Attribute Reference: %s' % (self.owner_id,
		return 'Id: %i, %s %i - %s %s' % (self.id,
					     #EntityType.objects.filter(id__exact=self.owner_type_id)[0],
					     self.MONTHS_OF_YEAR[int(self.start_month) - 1][1], self.start_day,
					     self.MONTHS_OF_YEAR[int(self.end_month) - 1][1], self.end_day
					     #self.get_start_month_display(), self.get_start_day_display(),
					     #self.get_end_month_display(), self.get_end_day_display()
					     		) 

	#owner_id = models.IntegerField()
	#owner_type = models.ForeignKey(EntityType)
	#start = models.DateField()
	start_month = models.IntegerField(choices=MONTHS_OF_YEAR)
	start_day = models.IntegerField()
	#end = models.DateField()
	end_month = models.IntegerField(choices=MONTHS_OF_YEAR)
	end_day = models.IntegerField()
	#closed = models.BooleanField()
	#editable = models.BooleanField()
	user_add_child = models.BooleanField(editable=False)
	child_type = models.IntegerField(choices=ATTRIB_TYPE, editable=False)

	class Admin:
		pass

	def compare(self, node_object):
		print 'In TimeOfYear, compare method'
		return generic_compare(self, node_object)

	def copy(self):
		print 'In TimeOfYear, copy method'
		return generic_copy(self)

	def get_leaf_render(self, treestruct_id):
		#print 'In TimeOfYear, get_leaf_render() '
		render = '%s %i - %s %i' % (self.MONTHS_OF_YEAR[self.start_month - 1][1], self.start_day,
					    self.MONTHS_OF_YEAR[self.end_month - 1][1], self.end_day)
		#render = '%s %i - %s %i %s' % (self.MONTHS_OF_YEAR[self.start_month - 1][1], self.start_day,
		#			    self.MONTHS_OF_YEAR[self.end_month - 1][1], self.end_day, self.closed and 'CLOSED' or ' ')
		if self.user_add_child:
			# Modified so that span has an id containing the treestruct_id, and button has and id containing the type of leaf.
			text = '<span id="%i" class="leaf">%s</span> <button name="Add %s" id="addleaf_%i" class="leafbutton">Add %s</button></button><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, render, self.get_child_type_display(), self.child_type, self.get_child_type_display(), treestruct_id)
		else:
			text = '<span id="%i" class="leaf">%s</span></button><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, render, treestruct_id)

		#render = '%s %i - %s %i' % (self.MONTHS_OF_YEAR[self.start_month - 1][1], self.start_day,
		#			    self.MONTHS_OF_YEAR[self.end_month - 1][1], self.end_day)
		return text
	
	def get_leaf_html(self, treestruct_id):
		return self.get_leaf_render(treestruct_id)
		
	def get_html(self, treestruct_id):
		#print 'In TimeOfYear get_html() '
		render = self.get_leaf_render(treestruct_id)
		#print render
		text = '<fieldset style="width:400px;">' + render + '</fieldset>'
		if self.user_add_child:
			node = {'text': text, 'id': str(treestruct_id), 'classes':'folder', 'hasChildren': 'true'}  # id is used to refer to node later.
		else:
			node = {'text': text, 'id': str(treestruct_id), 'classes':'folder'}  # id is used to refer to node later.
		return node

	def get_newform_html(cls):
		print 'In TimeOfYear get_newform_html'
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm()
		text = newform_header + thisform.as_p() + newform_footer
		return text
	get_newform_html = classmethod(get_newform_html)


	def save_newform_data(cls, thePOST, add_leaf=1):
		print 'In save_newform_data'
		print 'in TimeofYear save_form_data'
		if add_leaf is None:
			add_leaf = 1 # default
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm(thePOST)
		print 'After form creation'
		if thisform.is_valid():
			print 'POST data valid'
			thisform.full_clean()
			record = thisform.save(commit=False)
			print 'Past form save to temp record'
			new_rec = cls(start_month = int(record.start_month),
				      start_day = int(record.start_day),
				      end_month = int(record.end_month),
				      end_day = int(record.end_day),
				      #closed = record.closed,
				      #user_add_child = not record.closed,
				      user_add_child = True,
				      child_type = int(add_leaf)
				      #child_type = ATTRIB_TYPE[1][0]
				      )
			print 'Past creating new_rec'
			new_rec.save()
			#return new_rec
			errors = False
			text = 'Record Saved'
			print 'Record Saved'
		else: # form not valid.
			new_rec = -100
			errors = True
			print 'POST data invalid'
			text = newform_header + thisform.as_p() + newform_footer
			#print text
		return_data = {'html': text, 'errors': errors, 'new_rec': new_rec}
		return return_data

	save_newform_data = classmethod(save_newform_data)

	def get_form_html(self, treestruct_id):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		thisform = ThisForm(self.__dict__)
		text = form_header + thisform.as_p() + form_footer
		#node = {'text': text, 'id': str(treestruct_id)}  # id is used to refer to node later.
		return text

	def save_form_data(self, thePOST):
		print 'In save_form_data'
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		thisform = ThisForm(thePOST)
		print 'After form creation'
		if thisform.is_valid():
			print 'POST data valid'
			thisform.full_clean()
			record = thisform.save(commit=False)
			self.start_month = record.start_month
			self.start_day = record.start_day
			self.end_month = record.end_month
			self.end_day = record.end_day
			#self.closed = record.closed
			#self.user_add_child = not record.closed
			#self.user_add_child = True
			#self.child_type = ATTRIB_TYPE[1][0]
			self.save()
			html = '<h1 style="color:red;">Record Saved</h1>'
			return {'html': html, 'errors': False}
			#return '<h1 style="color:red;">Record Saved</h1>'
		else:
			print 'POST data invalid'
			text = form_header + thisform.as_p() + form_footer
			#print text
			return {'html': text, 'errors': True}



class DaysOfWeek(models.Model):
	"""
	Representation of the Days of the week.
	"""
	DAYS_OF_WEEK = (
		(0, 'Sunday'),
		(1, 'Monday'),
		(2, 'Tuesday'),
		(3, 'Wednesday'),
		(4, 'Thursday'),
		(5, 'Friday'),
		(6, 'Saturday')
		)
	"""
	DAYS_OF_WEEK = (
		('SU', 'Sunday'),
		('MO', 'Monday'),
		('TU', 'Tuesday'),
		('WE', 'Wednesday'),
		('TH', 'Thursday'),
		('FR', 'Friday')
		)
        """
	def __str__(self):
		if self.endday is not None:
			#return '%s - %s for %s' % (self.get_day_display(), self.get_endday_display(),
			return '%s - %s' % (self.DAYS_OF_WEEK[int(self.day)][1], self.DAYS_OF_WEEK[int(self.endday)][1])
					#	   TimeOfYear.objects.filter(id__exact=self.timeofyear_id)[0])
		else:
			return '%s' % (self.DAYS_OF_WEEK[int(self.day)][1])
					#      TimeOfYear.objects.filter(id__exact=self.timeofyear_id)[0])

	#day = models.CharField(max_length=2, choices=DAYS_OF_WEEK)
	day = models.IntegerField(choices=DAYS_OF_WEEK)
	#endday = models.CharField(max_length=2, choices=DAYS_OF_WEEK)
	endday = models.IntegerField(choices=DAYS_OF_WEEK,  null=True, blank=True)
	#day_range = models.BooleanField()
	closed = models.BooleanField()
	#timeofyear = models.ForeignKey(TimeOfYear)
	user_add_child = models.BooleanField(editable=False)
	child_type = models.IntegerField(choices=ATTRIB_TYPE, editable=False)

	class Admin:
		pass

	def compare(self, node_object):
		print 'In DaysOfWeek, compare method'
		return generic_compare(self, node_object)

	def copy(self):
		print 'In DaysOfWeek, copy method'
		return generic_copy(self)

	def get_leaf_render(self, treestruct_id):
		print 'In DaysOfWeek get_leaf_render'
		print 'endday'
		print self.endday
		if self.endday is not None:
			#render = '%s - %s' % (self.get_day_display(), self.get_endday_display())
			render = '%s - %s %s' % (self.DAYS_OF_WEEK[int(self.day)][1], self.DAYS_OF_WEEK[int(self.endday)][1], self.closed and 'CLOSED' or ' ')
		else:
			#render = self.get_day_display()
			#render = self.DAYS_OF_WEEK[int(self.day)][1]
			render = '%s %s' % (self.DAYS_OF_WEEK[int(self.day)][1], self.closed and 'CLOSED' or ' ')
		if self.user_add_child:
			# Modified so that span has an id containing the treestruct_id, and button has and id containing the type of leaf.
			text = '<span id="%i" class="leaf">%s</span> <button name="Add %s" id="addleaf_%i" class="leafbutton">Add %s</button</button><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, render, self.get_child_type_display(), self.child_type, self.get_child_type_display(), treestruct_id)

		else:
			text = '<span id="%i" class="leaf">%s</span></button><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, render, treestruct_id)
		return text

	def get_leaf_html(self, treestruct_id):
		print 'In DaysOfWeek get_leaf_html'
		return self.get_leaf_render(treestruct_id)

	def get_html(self, treestruct_id):
		render_text = self.get_leaf_render(treestruct_id)
		text = '<fieldset style="width:400px;">' + render_text + '</fieldset>'
		if self.user_add_child:
			node = {'text': text, 'id': str(treestruct_id), 'classes':'folder', 'hasChildren': 'true'}  # id is used to refer to node later.
		else:
			node = {'text': text, 'id': str(treestruct_id), 'classes':'folder'}  # id is used to refer to node later.
		return node
	        

	def get_newform_html(cls):
		print 'In DaysofWeek get_newform_html'
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm()
		text = newform_header + thisform.as_p() + newform_footer
		return text
	get_newform_html = classmethod(get_newform_html)

	def save_newform_data(cls, thePOST, add_leaf):
		print 'In DaysOfWeek save_form_data'
		if add_leaf is None:
			add_leaf = 2
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm(thePOST)
		print 'After form creation'
		if thisform.is_valid():
			print 'POST data valid'
			thisform.full_clean()
			record = thisform.save(commit=False)
			#print record.day_range
			print 'Past form save to temp record'
			new_rec = cls(day = int(record.day),
				      endday = record.endday,
				      closed = record.closed,
				      #day_range = record.day_range,
				      user_add_child = not record.closed,
				      child_type = int(add_leaf)
				      #child_type = ATTRIB_TYPE[2][0]
				      )
			print 'Past creating new_rec'
			new_rec.save()
			#return new_rec
			errors = False
			text = 'Record Saved'
			print 'Record Saved'
		else: # form not valid.
			new_rec = -100
			errors = True
			print 'POST data invalid'
			text = newform_header + thisform.as_p() + newform_footer
			#print text
		return_data = {'html': text, 'errors': errors, 'new_rec': new_rec}
		return return_data

	save_newform_data = classmethod(save_newform_data)

	def get_form_html(self, treestruct_id):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		thisform = ThisForm(self.__dict__)
		text = form_header + thisform.as_p() + form_footer
		#node = {'text': text, 'id': str(treestruct_id)}  # id is used to refer to node later.
		return text

	def save_form_data(self, thePOST):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		thisform = ThisForm(thePOST)
		if thisform.is_valid():
			thisform.full_clean()
			record = thisform.save(commit=False)
			self.day = record.day
			self.endday = record.endday
			self.closed = record.closed
			self.user_add_child = not record.closed
			#self.day_range = record.day_range
			#self.timeofyear = record.timeofyear
			#self.user_add_child = True,
			#self.child_type = ATTRIB_TYPE[2][0]
			self.save()
			html = '<h1 style="color:red;">Record Saved</h1>'
			return {'html': html, 'errors': False}
			#return '<h1 style="color:red;">Record Saved</h1>'
		else:
			print 'POST data invalid'
			text = form_header + thisform.as_p() + form_footer
			#print text
			return {'html': text, 'errors': True}

class HoursOfDay(models.Model):
	HOURS_OF_DAY = (
		(1, '1'),
		(2, '2'),
		(3, '3'),
		(4, '4'),
		(5, '5'),
		(6, '6'),
		(7, '7'),
		(8, '8'),
		(9, '9'),
		(10, '10'),
		(11, '11'),
		(12, '12'),
		)
	MORN_AFT = (
		(0, 'AM'),
		(1, 'PM') # if pm, add 12 to hours.
		)
	
	def __str__(self):
		return '%s:%s%s - %s:%s%s' % (self.HOURS_OF_DAY[int(self.start_hour)  - 1][1], self.start_min,
							     self.MORN_AFT[int(self.start_ampm)][1],
							     self.HOURS_OF_DAY[int(self.end_hour) - 1][1], self.end_min,
							     self.MORN_AFT[int(self.end_ampm)][1])
	
	#closed = models.BooleanField()
	start_hour = models.IntegerField(choices=HOURS_OF_DAY)
	start_min = models.CharField(max_length=2)
	start_ampm = models.IntegerField(choices=MORN_AFT, verbose_name='start am/pm')
	end_hour = models.IntegerField(choices=HOURS_OF_DAY)
	end_min = models.CharField(max_length=2)
	end_ampm = models.IntegerField(choices=MORN_AFT, verbose_name='end am/pm')
	user_add_child = models.BooleanField(editable=False)
	child_type = models.IntegerField(choices=ATTRIB_TYPE, null=True, blank=True, editable=False)

	def clean_start_min(self):
		start_min = self.clean_data.get('start_min', '')
		print 'In clean_start_min'
		print start_min
		raise forms.ValidationError('Test error')
	        return start_min

	class Admin:
		pass

	def compare(self, node_object):
		print 'In HoursOfDay, compare method'
		return generic_compare(self, node_object)

	def copy(self):
		print 'In HoursOfDay, copy method'
		return generic_copy(self)

	def get_leaf_render(self, treestruct_id):
		print 'In HoursOfDay get_leaf_render'
		render = '%s:%02d%s - %s:%02d%s' % (self.HOURS_OF_DAY[int(self.start_hour - 1)][1], int(self.start_min),
							     self.MORN_AFT[int(self.start_ampm)][1],
							     self.HOURS_OF_DAY[int(self.end_hour) - 1][1], int(self.end_min),
							     self.MORN_AFT[int(self.end_ampm)][1])

		if self.user_add_child:
			# Modified so that span has an id containing the treestruct_id, and button has and id containing the type of leaf.
			text = '<span id="%i" class="leaf">%s</span> <button name="Add %s" id="addleaf_%i" class="leafbutton">Add %s</button><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, render, self.get_child_type_display(), self.child_type, self.get_child_type_display(), treestruct_id)

		else:
			text = '<span id="%i" class="leaf">%s</span><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, render, treestruct_id)
		return text


	def get_leaf_html(self, treestruct_id):
		print 'In HoursOfDay get_leaf_html'
		return self.get_leaf_render(treestruct_id)

	def get_html(self, treestruct_id):
		render_text = self.get_leaf_render(treestruct_id)
		text = '<fieldset style="width:300px;">' + render_text + '</fieldset>'
		if self.user_add_child:
			node = {'text': text, 'id': str(treestruct_id), 'classes':'folder', 'hasChildren': 'true'}  # id is used to refer to node later.
		else:
			node = {'text': text, 'id': str(treestruct_id), 'classes':'folder'}  # id is used to refer to node later.
		return node

	def get_newform_html(cls):
		print 'In HoursofDay get_newform_html'
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm()
		text = newform_header + thisform.as_p() + newform_footer
		return text
	get_newform_html = classmethod(get_newform_html)

	def save_newform_data(cls, thePOST, add_leaf=None):
		print 'In HoursOfDay save_form_data'
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm(thePOST)
		print 'After form creation'
		if thisform.is_valid():
			print 'POST data valid'
			thisform.full_clean()
			record = thisform.save(commit=False)
			#print record.day_range
			print 'Past form save to temp record'
			new_rec = cls(
				      start_hour = int(record.start_hour),
				      start_min = int(record.start_min),
				      start_ampm = int(record.start_ampm),
				      end_hour = int(record.end_hour),
				      end_min = int(record.end_min),
				      end_ampm = int(record.end_ampm),
				      user_add_child = False,
				      #child_type = ATTRIB_TYPE[2][0]
				      )
			print 'Past creating new_rec'
			new_rec.save()
			errors = False
			text = 'Record Saved'
			print 'Record Saved'
		else: # form not valid.
			new_rec = -100
			errors = True
			print 'POST data invalid'
			text = newform_header + thisform.as_p() + newform_footer
			#print text
		return_data = {'html': text, 'errors': errors, 'new_rec': new_rec}
		return return_data
		#return new_rec
	save_newform_data = classmethod(save_newform_data)

	def get_form_html(self, treestruct_id):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		class EnhanceThisForm(ThisForm):
			def clean_start_min(self):
				#print 'in clean_start_min'
				data = self.cleaned_data['start_min']
				if not data.isdigit():
					raise ValidationError, _("Non-numeric characters aren't allowed here.")
				return data
				
		thisform = EnhanceThisForm(self.__dict__)
		text = form_header + thisform.as_p() + form_footer
		#node = {'text': text, 'id': str(treestruct_id)}  # id is used to refer to node later.
		return text

	def save_form_data(self, thePOST):
		print 'In HoursOfDay, save_form_data'
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		class EnhanceThisForm(ThisForm):
			def clean_start_min(self):
				#print 'in clean_start_min'
				data = self.cleaned_data['start_min']
				#print data
				if not data.isdigit():
					raise ValidationError, _("Non-numeric characters aren't allowed here.")
				return data
		thisform = EnhanceThisForm(thePOST)
		if thisform.is_valid():
			print 'POST data is valid'
			thisform.full_clean()
			record = thisform.save(commit=False)
			self.start_hour = record.start_hour
			self.start_min = record.start_min
			self.start_ampm = record.start_ampm
			self.end_hour = record.end_hour
			self.end_min = record.end_min
			self.end_ampm = record.end_ampm
			self.user_add_child = False
			#self.child_type = record.child_type
			self.save()
			html = '<h1 style="color:red;">Record Saved</h1>'
			return {'html': html, 'errors': False}
			#return '<h1 style="color:red;">Record Saved</h1>'
		else:
			print 'POST data invalid'
			text = form_header + thisform.as_p() + form_footer
			#print text
			return {'html': text, 'errors': True}

class SpecialDay(models.Model):
	def __str__(self):
		return self.name

	# Changed Feb. 7, 2009 to accomodate the back end tables.
	#code = models.CharField(max_length=2, primary_key=True)
	code = models.SmallIntegerField(primary_key=True)
	name = models.CharField(max_length=30)

	class Admin:
		pass
"""
class SpecialDay(models.Model):
	def __str__(self):
		return self.name

	special_day_key = models.IntegerField(primary_key=True)
	special_day_desc = models.TextField()

	class Admin:
		pass
        class Meta:
            db_table = u'special_day'
"""

class SpecialDate(models.Model):
	def __str__(self):
		return self.specialdate_id.name
		#return self.get_specialdate_id_display()

	specialdate_id = models.ForeignKey(SpecialDay, db_column='code', verbose_name='Special Day')
	closed = models.BooleanField()
	user_add_child = models.BooleanField(editable=False)
	child_type = models.IntegerField(choices=ATTRIB_TYPE, editable=False)

	def compare(self, node_object):
		print 'In SpecialDate, compare method'
		return generic_compare(self, node_object)

	def copy(self):
		print 'In SpecialDate, copy method'
		return generic_copy(self)

	def get_leaf_render(self, treestruct_id):
		if self.user_add_child:
			#child_type_text = ATTRIB_TYPE[self.child_type_id - 1][1]
			# Modified so that span has an id containing the treestruct_id, and button has and id containing the type of sub-leaf (TimeOfYear) that can be added.
			html = '<span id="%i" class="leaf">%s %s</span> <button name="Add %s" id="addleaf_%i" class="leafbutton">Add %s</button><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, self.specialdate_id, self.closed and 'CLOSED' or ' ', self.get_child_type_display(), self.child_type, self.get_child_type_display(), treestruct_id)
		else:
			html = '<span id="%i" class="leaf">%s %s</span><button name="delete" id="%i" class="delete"><img src="/bookitnow_media/trashcan.png" alt="Delete"/></button>' % (treestruct_id, self.specialdate_id, self.closed and 'CLOSED' or ' ', treestruct_id)

		return html
		
	def get_leaf_html(self, treestruct_id):
		return self.get_leaf_render(treestruct_id)
	
	def get_html(self, treestruct_id):
		html_text = self.get_leaf_render(treestruct_id)
		html = '<fieldset style="width:300px;">' + html_text + '</fieldset>'
		if self.user_add_child:
			node = {'text': html, 'id': str(treestruct_id), 'classes':'folder', 'hasChildren': 'true'}  # id is used to refer to node later.
		else:
			node = {'text': html, 'id': str(treestruct_id), 'classes':'folder'}  # id is used to refer to node later.
		return node

	def get_newform_html(cls):
		print 'In SpecialDate get_newform_html'
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm()
		text = newform_header + thisform.as_p() + newform_footer
		return text
	get_newform_html = classmethod(get_newform_html)

	def save_newform_data(cls, thePOST, add_leaf=None):
		print 'In SpecialDate save_newform_data'
		if add_leaf is None:
			add_leaf = 2 # default
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm(thePOST)
		print 'After form creation'
		if thisform.is_valid():
			print 'POST data valid'
			thisform.full_clean()
			record = thisform.save(commit=False)
			print record.specialdate_id_id
			print add_leaf
			print 'Past form save to temp record'
			# Note that you have to append and '_id' to the name for Foreign Keys to get the id.
			new_rec = cls(specialdate_id_id = int(record.specialdate_id_id),
				      closed = record.closed,
				      user_add_child = not record.closed,
				      child_type = add_leaf
				      #child_type = ATTRIB_TYPE[4][0]
				      )
			print 'Past creating new_rec'
			new_rec.save()
			#return new_rec
			errors = False
			text = 'Record Saved'
			print 'Record Saved'
		else: # form not valid.
			new_rec = -100
			errors = True
			print 'POST data invalid'
			text = newform_header + thisform.as_p() + newform_footer
			#print text
		return_data = {'html': text, 'errors': errors, 'new_rec': new_rec}
		return return_data

	save_newform_data = classmethod(save_newform_data)

	def get_form_html(self, treestruct_id):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		# Need to do this because of Foreign Key
		field_values = dict(self.__dict__)
		#print 'field_values:'
		#print field_values
		#print 'specialdate_id_id:'
		#print field_values['specialdate_id_id']
		field_values['specialdate_id'] = self.specialdate_id_id
		thisform = ThisForm(field_values)
		text = form_header + thisform.as_p() + form_footer
		#node = {'text': text, 'id': str(treestruct_id)}  # id is used to refer to node later.
		return text

	def save_form_data(self, thePOST):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		thisform = ThisForm(thePOST)
		if thisform.is_valid():
			thisform.full_clean()
			record = thisform.save(commit=False)
			self.specialdate_id = record.specialdate_id
			self.closed = record.closed
			self.user_add_child = not record.closed
			#self.child_type = ATTRIB_TYPE[2][0]
			self.save()
			html = '<h1 style="color:red;">Record Saved</h1>'
			return {'html': html, 'errors': False}
			#return '<h1 style="color:red;">Record Saved</h1>'
		else:
			print 'POST data invalid'
			text = form_header + thisform.as_p() + form_footer
			#print text
			return {'html': text, 'errors': True}

	class Admin:
		pass

class TextString(models.Model):
	def __str__(self):
		return self.string_text
	
	string_text = models.CharField(max_length=60)
	user_add_child = models.BooleanField()
	child_type = models.IntegerField(choices=ATTRIB_TYPE)

	def compare(self, node_object):
		print 'In TextString, compare method'
		return generic_compare(self, node_object)

	def copy(self):
		print 'In TextString, copy method'
		return generic_copy(self)

	def get_leaf_render(self, treestruct_id):
		if self.user_add_child:
			#child_type_text = ATTRIB_TYPE[self.child_type_id - 1][1]
			# Modified so that span has an id containing the treestruct_id, and button has and id containing the type of sub-leaf (TimeOfYear) that can be added.
			html = '<span id="%i" class="leaf">%s</span> <button name="Add %s" id="addleaf_%i" class="leafbutton">Add %s</button>' % (treestruct_id, self.string_text, self.get_child_type_display(), self.child_type, self.get_child_type_display())
		else:
			html = '<span id="%i" class="leaf">%s</span>' % (treestruct_id, self.string_text)

		return html
		
	def get_leaf_html(self, treestruct_id):
		return self.get_leaf_render(treestruct_id)
	
	def get_html(self, treestruct_id):
		html_text = self.get_leaf_render(treestruct_id)
		html = '<fieldset style="width:350px;">' + html_text + '</fieldset>'
		if self.user_add_child:
			node = {'text': html, 'id': str(treestruct_id), 'classes':'folder', 'hasChildren': 'true'}  # id is used to refer to node later.
		else:
			node = {'text': html, 'id': str(treestruct_id), 'classes':'folder'}  # id is used to refer to node later.
		return node

	def get_newform_html(cls):
		print 'In TextString get_newform_html'
		#ThisForm = form_for_model(cls)
		class ThisForm(ModelForm):
		    class Meta:
		        model = cls

		thisform = ThisForm()
		text = newform_header + thisform.as_p() + newform_footer
		return text
	get_newform_html = classmethod(get_newform_html)


	def get_form_html(self, treestruct_id):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		#field_values = dict(self.__dict__)
		#field_values['child_type_id'] = self.child_type
		thisform = ThisForm(self.__dict__)
		text = form_header + thisform.as_p() + form_footer
		#node = {'text': text, 'id': str(treestruct_id)}  # id is used to refer to node later.
		return text

	def save_form_data(self, thePOST):
		#self.ThisForm = form_for_model(self.__class__)
		class ThisForm(ModelForm):
		    class Meta:
		        model = self.__class__

		thisform = ThisForm(thePOST)
		if thisform.is_valid():
			thisform.full_clean()
			record = thisform.save(commit=False)
			self.string_text = record.string_text
			#self.user_add_child =True
			#self.child_type = ATTRIB_TYPE[2][0]
			self.save()
			html = '<h1 style="color:red;">Record Saved</h1>'
			return {'html': html, 'errors': False}
			#return '<h1 style="color:red;">Record Saved</h1>'
		else:
			print 'POST data invalid'
			text = form_header + thisform.as_p() + form_footer
			#print text
			return {'html': text, 'errors': True}

	class Admin:
		pass

##################################################################
# End of Configuration treeview Models
##################################################################

class QuickAvailTimes(object):

	def __str__(self):
		return self.sp_key

	def __init__(self, sp_key=None, locn_key=None, resource_key=None, eff_date=None, top_of_sched_tmstmp=None, band_indx=None ):
		self.sp_key = sp_key
		self.locn_key = locn_key
		self.resource_key = resource_key
		self.eff_date = eff_date
		self.top_of_sched_tmstmp = top_of_sched_tmstmp
		self.band_indx = band_indx

	def setup(self):
		param_list = ["sp_key", "locn_key", "resource_key", "eff_date::date", "top_of_sched_tmstmp::timestamp"
		            , "band_indx::smallint"]
		stored_proc = StoredProc("f_quick_avail_times", param_list)
		self.alchExec = stored_proc.alchModify
	
	def localExec(self):
		"""
		This method executes the stored proc
		"""
		if not self.__dict__.has_key('alchExec'):
		     self.setup()
		(myresult, error_result) = self.alchExec(self.__dict__)
		return (myresult, error_result)
	
