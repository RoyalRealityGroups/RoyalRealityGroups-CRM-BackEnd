
from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from import_export.formats import base_formats
from import_export.tmp_storages import TempFolderStorage




from .serializers import GenericImportExportSerializer, GenericImportSerializer, GenericConfirmImportSerializer
from .import_export_models import only_import_models




import pandas as pd



def get_model_class(model_name):
    
    model = None
    SerializerClass = None
    queryset = None

    import_models = only_import_models
    if model_name in import_models.keys() :
        print('model_name:', model_name)
        model = import_models[model_name]['model_class']
        SerializerClass = import_models[model_name].get('serializer_class', None )
        queryset = import_models[model_name].get('queryset', None )
        if import_models[model_name].get('import_type',1) == 1:
            model = None


    return (model, SerializerClass, queryset)



# def write_to_tmp_storage(filename, import_file,):
#     tmp_storage = TempFolderStorage(name= filename)

#     data = bytes()
#     for chunk in import_file.chunks():
#         data += chunk

#     tmp_storage.save(data, 'r' )
#     return tmp_storage

# class FileUploadView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [FileUploadParser]

#     def post(self, request, filename, format=None):
#         file_obj = request.data['file']

#         print(file_obj, type(file_obj))
#         if file_obj:
#             print(file_obj.read().decode('utf-8'), type(file_obj))
#             tmp_storage = write_to_tmp_storage(filename, file_obj)
#             # df = pd.read_csv(io.StringIO(file_obj.read().decode('utf-8')),)
#             # usecols=["Code", "Date", "user", "Counter", "Counter Code", "Party Type", "Purchase Type", "Customer", "Customer Code", "Vehicle No", "VehicleNo Code", "Sale", "Vehicle Reading", "Color", "Color Code", "Is Custom Color", "Custom Color", "Dealer", "Dealer Code", "Hypothecation", "Hypothecationisinternal", "Internal Financier Name", "Internal Financier Code", "External Financier Name", "Loan Status", "Loan Number", "Loan Amount", "Financier Bank", "Financier Bank Code", "Financier Mobile", "Financier Account Number", "Financier Ifsccode", "Token Status", "Token Date", "Token Number", "Insurance Status", "Insurance Company", "Insurance Company Code", "Insurance Number", "Insurance Expdate", "Insurance Amount", "Purchase Rate", "Tyre", "Battery", "Engine Repair", "Outlook Repair", "Total Repair Amount", "Echallan", "Consultancy Charges", "Customer Credit Amount", "Customer Bank Amount", "Customer Cash Amount", "Showminimum Sale Amount", "Rto Charges", "Minimum Sale Amount", "Special Incentive", "Mc Internal Type", "Mc internal Name", "Mc internal Code", "External Mc Name", "External Mc Mobile", "External Mc Bank", "External Mc Bank Code", "External Mc Ifsccode", "External Mc Bankacno", "Payment To", "Customer Payble Amount", "Mc Amount", "Re Estimation", "Total", "Fsync", "Approved Level", "Approval Status", "Approved By", "Approved On", "Availability", "Estimation", "Address Proof1", "Address Proof1 Code", "Address Proof2", "Address Proof2 Code", "Created By", "Created On", "Modified On", "Modified By"]
#             # df = pd.read_csv(io.StringIO(file_obj.read().decode('utf-8'),), )
#             df = pd.read_csv(tmp_storage.get_full_path() )
#             print(df)
#         else:
#             return Response( 'No file to process! Please upload a file to process.')



class ImportView(APIView):
    permission_classes = [AllowAny]
    # SerializerClass = GenericImportSerializer
    formats = base_formats.DEFAULT_FORMATS
    from_encoding = "utf-8"

    
    def write_to_tmp_storage(self, import_file, input_format):
        tmp_storage = TempFolderStorage()
        data = bytes()
        for chunk in import_file.chunks():
            data += chunk

        tmp_storage.save(data, input_format.get_read_mode())
        return tmp_storage

    
    def format_row(self, index, row, import_fields, outobj={}, Notfoundlist=[]):
        for field in import_fields:
            try:
                if field.get("is_serializer", False) and not field.get("is_serializer_many", False): # if many False
                    Notfoundlist, outobj[field["key"]] = self.format_row(index, row, field["serializer_fields"], {}, Notfoundlist)
                elif field.get("is_serializer", False) and field.get("is_serializer_many", False): # if many True
                    Notfoundlist, obj = self.format_row(index, row, field["serializer_fields"], {}, Notfoundlist)
                    outobj[field["key"]] = [obj,]
                else:
                    outobj[field["key"]] =row[field["label"]]

            except KeyError:
                Notfoundlist.append(field["label"]) 
        
        # print(index, len(Notfoundlist))
        return (Notfoundlist, outobj )

    def get_field_by_key(self, import_fields, key):
        return next((sub for sub in import_fields if sub['key'] == key), None)

    def get_instance(self, queryset, import_fields, SerializerClass, row):
        params = {}
        for key in self.get_import_id_fields(SerializerClass):
            field = self.get_field_by_key(import_fields, key)
            params[key] = row[field["label"]]
        if params:
            try:
                return queryset.get(**params)
            except:
                return None
        else:
            return None

    def get_import_id_fields(self, SerializerClass):
        if hasattr(SerializerClass.Meta, "import_id_fields"):
            return SerializerClass.Meta.import_id_fields
        else:
            return ( 'id', )

    def import_dataframe(self, model, SerializerClass, queryset, request, df, import_fields, dryrun= True ):
        data_list = []
        has_errors = False
        for index, row in df.iterrows():
            NotFoundKeys, data_obj = self.format_row(index, row, import_fields, {}, [] )
            # queryset = State.objects.all()
            instance = self.get_instance(queryset, import_fields, SerializerClass, row)
            # print("instance", instance)
            
            serializer_context = { 'request' : request }

            serializer = SerializerClass(data= data_obj, instance= instance, many= False, context= serializer_context )
            is_valid = serializer.is_valid(raise_exception=False)
            if not is_valid :
                has_errors = True
            elif dryrun == False:
                serializer.save()
            
            data_list.append({
                # "input": data_obj,
                "import_status":  "New" if instance == None else "Update" ,
                "has_errors": not is_valid,
                "errors": serializer.errors,
                "validated_data": serializer.validated_data,
                "output_data": serializer.data,
                "keys_notfound": NotFoundKeys,
            })
        return (data_list, has_errors)
        
    def post(self, request, *args, **kwargs):
        dryrun = kwargs['dryrun']
        
        model = None
        SerializerClass = None
        queryset = None

        import_formats = [f for f in self.formats if f().can_import()]
        
        serializer = GenericImportExportSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            model_name = serializer.validated_data['model_name']
            model, SerializerClass, queryset = get_model_class(model_name)
           
        if model is None:
            return Response({"error":"Invalid Model type" }, status=400)
        
        
        # permission = GetPermission(model._meta.app_label + ".import_"+ model._meta.model_name)()
        # if not permission.has_permission(request, self):
        #     return Response({"error":"You do not have permission to perform this action." }, status=403)


        if SerializerClass is None:
            return Response({"error":"Invalid Model Serializer type" }, status=400)

        if dryrun == 'dryrun':
            serializer = GenericImportSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                cleaned_data = serializer.validated_data
        elif dryrun == 'process':
            serializer = GenericConfirmImportSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                cleaned_data = serializer.validated_data
        else:
            cleaned_data = {}
            return Response({"error":"Invalid Dryrun type" }, status=400)

        try:
            input_format = import_formats[
                cleaned_data['input_format']
            ]()
            # import_file = cleaned_data['import_file']
            # tmp_storage = self.write_to_tmp_storage(import_file, input_format)
            # import_file_name = import_file.name
            # data = tmp_storage.read('r')
            
            if dryrun == 'dryrun':
                import_file = cleaned_data['import_file']
                tmp_storage = self.write_to_tmp_storage(import_file, input_format)
                import_file_name = import_file.name
                original_file_name = import_file.name
            if dryrun == 'process':
                tmp_storage = TempFolderStorage(name=cleaned_data['import_file_name'])
                import_file_name = cleaned_data['import_file_name']
                original_file_name = cleaned_data['original_file_name']
            

            import_fields = SerializerClass.Meta.import_fields
            print("import_fields", import_fields)

            df = pd.read_csv(tmp_storage.get_full_path() )
            
        except UnicodeDecodeError as e:
            return JsonResponse({"error":"Imported file has a wrong encoding: %s" % e })
        except Exception as e:
            return JsonResponse({"error":"%s : %s , encountered while trying to read file: %s" % (type(e).__name__, e, import_file_name)})
        
        data_list, has_errors = self.import_dataframe( model, SerializerClass, queryset, request, df, import_fields, dryrun = True )
            # print(df)
        initial= {
            'import_file_name': tmp_storage.name,
            'original_file_name': original_file_name,
            'input_format': cleaned_data['input_format'],
        }
        if dryrun == 'process' and has_errors == False:
            data_list = self.import_dataframe( model, SerializerClass, queryset, request, df, import_fields, dryrun = False )

            
        # print("data_list", data_list)

        return Response( {'initial': initial, 'data_list': data_list, "has_errors" : has_errors})



