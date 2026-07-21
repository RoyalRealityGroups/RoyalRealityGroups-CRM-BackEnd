from django.urls import path
from . import views

urlpatterns = [

    # Channel Partner Configuration
    path('channel-config/', views.ChannelPartnerConfigurationView.as_view()),

    # Generic Channel Partner URLs (for combined access)
    path('channel-partners/mini/', views.ChannelPartnerMiniList.as_view()),
    path('channel-partners/<str:pk>/', views.ChannelPartnerDetail.as_view()),

    # path('state/', views.StateList.as_view()),
    # path("state/<str:pk>", views.StateDetail.as_view()),
    # path('states/mini/', views.StateMini.as_view()),
    # path('states/list/', views.StateMiniList.as_view()),

    
    # path('locations/', views.LocationList.as_view()),

    # Country URLs
    path('countries/', views.CountryList.as_view()),
    path('countries/mini/', views.CountryMiniList.as_view()),
    path('countries/<str:pk>/', views.CountryDetail.as_view()),
    
    # State URLs
    path('states/', views.StateList.as_view()),
    path('states/mini/', views.StateMiniList.as_view()),
    path('states/<str:pk>/', views.StateDetail.as_view()),
    
    # District URLs
    path('districts/', views.DistrictList.as_view()),
    path('districts/mini/', views.DistrictMiniList.as_view()),
    path('districts/<str:pk>/', views.DistrictDetail.as_view()),
    
    # Mandal URLs
    path('mandals/', views.MandalList.as_view()),
    path('mandals/mini/', views.MandalMiniList.as_view()),
    path('mandals/<str:pk>/', views.MandalDetail.as_view()),
    
    # City URLs
    path('cities/', views.CityList.as_view()),
    path('cities/mini/', views.CityMiniList.as_view()),
    path('cities/<str:pk>/', views.CityDetail.as_view()),
    
    # Area URLs
    path('areas/', views.AreaList.as_view()),
    path('areas/mini/', views.AreaMiniList.as_view()),
    path('areas/<str:pk>/', views.AreaDetail.as_view()),

    # Route URLs
    path('routes/', views.RouteList.as_view()),
    path('routes/mini/', views.RouteMiniList.as_view()),
    path('routes/<str:pk>/', views.RouteDetail.as_view()),
    
    # Company URLs
    path('companies/', views.CompanyList.as_view()),
    path('companies/mini/', views.CompanyMiniList.as_view()),
    path('companies/<str:pk>/', views.CompanyDetail.as_view()),
    
    # Location URLs
    path('locations/mini/', views.LocationMiniList.as_view()),
    path('locations/', views.LocationList.as_view()),
    path('locations/<str:pk>/', views.LocationDetail.as_view()),
    path('locations/<str:location_id>/contacts/', views.LocationContactList.as_view()),
    path('locations/<str:location_id>/contacts/<str:pk>/', views.LocationContactDetail.as_view()),
    
    # WareHouse URLs
    path('warehouses/', views.WareHouseList.as_view()),
    path('warehouses/mini/', views.WareHouseMiniList.as_view()),
    path('warehouses/<str:pk>/', views.WareHouseDetail.as_view()),
    



    path('uom/mini/', views.UOMMini.as_view()),
    path('uom/', views.UOMList.as_view()),
    path('uom/<str:pk>/', views.UOMDetail.as_view()),

    # Category URLs
    path('categories/', views.CategoryList.as_view()),
    path('categories/mini/', views.CategoryMini.as_view()),
    path('categories/<str:pk>/', views.CategoryDetail.as_view()),
    
    # Brand URLs
    path('brands/', views.BrandList.as_view()),
    path('brands/mini/', views.BrandMini.as_view()),
    path('brands/<str:pk>/', views.BrandDetail.as_view()),

    # Tax URLs
    path('taxes/', views.TaxList.as_view()),
    path('taxes/mini/', views.TaxMini.as_view()),
    path('taxes/<str:pk>/', views.TaxDetail.as_view()),

    # Item Tax Composition URLs
    path('item-tax-compositions/', views.ItemTaxCompositionList.as_view()),
    path('item-tax-compositions/<str:pk>/', views.ItemTaxCompositionDetail.as_view()),
    path('items/<str:item_id>/current-tax-composition/', views.ItemCurrentTaxComposition.as_view()),

    # OutletType URLs
    path('outlet-types/', views.OutletTypeList.as_view()),
    path('outlet-types/mini/', views.OutletTypeMini.as_view()),
    path('outlet-types/<str:pk>/', views.OutletTypeDetail.as_view()),

    # Agent/Broker URLs
    path('agents/', views.AgentList.as_view()),
    path('agents/mini/', views.AgentMini.as_view()),
    path('agents/<str:pk>/', views.AgentDetail.as_view()),

    # Item URLs
    path('items/', views.ItemList.as_view()),
    path('items/mini/', views.ItemMini.as_view()),
    path('items/bulk-tax-update/', views.BulkTaxUpdateView.as_view()),
    path('items/barcode-search/', views.ItemBarcodeSearch.as_view()),
    path('items/<str:pk>/', views.ItemDetail.as_view()),

    # Item Tax Mapping URLs

    # Item UOM Conversion URLs
    path('item-uom-conversions/', views.ItemUOMConversionList.as_view()),
    path('item-uom-conversions/<str:pk>/', views.ItemUOMConversionDetail.as_view()),

    # Item Field Configuration URLs
    path('item-field-config/', views.ItemFieldConfigurationListAPIView.as_view()),
    path('item-field-config/bulk-update/', views.ItemFieldConfigurationBulkUpdateAPIView.as_view()),

    # Superstockist URLs
    path('superstockists/', views.SuperstockistList.as_view()),
    path('superstockists/mini/', views.SuperstockistMini.as_view()),
    path('superstockists/<str:pk>/', views.SuperstockistDetail.as_view()),
    path('superstockists/<str:pk>/attachments/', views.SuperstockistAttachmentList.as_view()),
    path('superstockists/<str:pk>/upload_attachment/', views.SuperstockistAttachmentUpload.as_view()),
    path('superstockists/<str:pk>/attachments/<str:attachment_id>/', views.SuperstockistAttachmentDelete.as_view()),
    path('superstockists/<str:superstockist_id>/locations/', views.SuperstockistLocationList.as_view()),
    path('superstockists/<str:superstockist_id>/locations/bulk/', views.SuperstockistLocationBulk.as_view()),
    path('superstockists/<str:superstockist_id>/locations/<str:pk>/', views.SuperstockistLocationDetail.as_view()),
    path('superstockists/<str:superstockist_id>/contacts/', views.SuperstockistContactList.as_view()),
    path('superstockists/<str:superstockist_id>/contacts/<str:pk>/', views.SuperstockistContactDetail.as_view()),

    # Distributor URLs
    path('distributors/', views.DistributorList.as_view()),
    path('distributors/mini/', views.DistributorMini.as_view()),
    path('distributors/<str:pk>/', views.DistributorDetail.as_view()),
    path('distributors/<str:pk>/attachments/', views.DistributorAttachmentList.as_view()),
    path('distributors/<str:pk>/upload_attachment/', views.DistributorAttachmentUpload.as_view()),
    path('distributors/<str:pk>/attachments/<str:attachment_id>/', views.DistributorAttachmentDelete.as_view()),
    path('distributors/<str:distributor_id>/locations/', views.DistributorLocationList.as_view()),
    path('distributors/<str:distributor_id>/locations/bulk/', views.DistributorLocationBulk.as_view()),
    path('distributors/<str:distributor_id>/locations/<str:pk>/', views.DistributorLocationDetail.as_view()),
    path('distributors/<str:distributor_id>/contacts/', views.DistributorContactList.as_view()),
    path('distributors/<str:distributor_id>/contacts/<str:pk>/', views.DistributorContactDetail.as_view()),

    # Retailer URLs
    path('retailers/', views.RetailerList.as_view()),
    path('retailers/mini/', views.RetailerMini.as_view()),
    path('retailers/<str:pk>/', views.RetailerDetail.as_view()),
    path('retailers/<str:pk>/attachments/', views.RetailerAttachmentList.as_view()),
    path('retailers/<str:pk>/upload_attachment/', views.RetailerAttachmentUpload.as_view()),
    path('retailers/<str:pk>/attachments/<str:attachment_id>/', views.RetailerAttachmentDelete.as_view()),
    path('retailers/<str:retailer_id>/locations/', views.RetailerLocationList.as_view()),
    path('retailers/<str:retailer_id>/locations/<str:pk>/', views.RetailerLocationDetail.as_view()),
    path('retailers/<str:retailer_id>/contacts/', views.RetailerContactList.as_view()),
    path('retailers/<str:retailer_id>/contacts/<str:pk>/', views.RetailerContactDetail.as_view()),

    # Price Book Document URLs (Document-centric)
    path('price-book-documents/', views.PriceBookDocumentList.as_view()),
    path('price-book-documents/<str:pk>/', views.PriceBookDocumentDetail.as_view()),
    path('price-book-documents/<str:pk>/update/', views.PriceBookDocumentUpdate.as_view()),
    path('price-book-documents/<str:pk>/delete/', views.PriceBookDocumentDelete.as_view()),
    # Price Book URLs (Entry-centric - legacy)
    path('price-books/', views.PriceBookList.as_view()),
    path('price-books/mini/', views.PriceBookMini.as_view()),
    path('price-books/generate-document-number/', views.GeneratePriceBookDocumentNumber.as_view()),
    path('price-books/bulk-create/', views.PriceBookBulkCreate.as_view()),
    path('price-books/load-grid-with-parents/', views.PriceBookLoadGridWithParents.as_view()),
    path('price-books/history/', views.PriceBookHistoryList.as_view()),
    path('price-books/get-price/', views.GetItemPrice.as_view()),
    path('price-books/<str:pk>/', views.PriceBookDetail.as_view()),
    
    # Price Book Document Actions
    path('price-book-documents/<str:document_id>/finalize/', views.PriceBookDocumentFinalize.as_view()),
    path('price-book-documents/<str:document_id>/duplicate-as-draft/', views.PriceBookDocumentDuplicateAsDraft.as_view()),

    # Scheme URLs
    path('schemes/', views.SchemeListCreateView.as_view()),
    path('schemes/mini/', views.SchemeMiniList.as_view()),
    path('schemes/choices/', views.SchemeChoicesView.as_view()),
    path('schemes/<str:pk>/', views.SchemeDetailView.as_view()),
    path('schemes/<str:pk>/activate/', views.SchemeActivateView.as_view()),
    path('schemes/<str:pk>/deactivate/', views.SchemeDeactivateView.as_view()),
    path('schemes/<str:scheme_id>/history/', views.SchemeHistoryView.as_view()),

    # ============================================================================
    # SALES ORDER URLs MOVED TO Sales APP
    # ============================================================================
    # Sales Order endpoints have been moved to /api/sales/ instead of /api/masters/
    # The new URLs are:
    #   - /api/sales/orders/
    #   - /api/sales/orders/<pk>/
    #   - /api/sales/orders/<pk>/approve/
    #   - /api/sales/orders/<pk>/reject/
    #   - /api/sales/orders/<pk>/process/
    #   - /api/sales/orders/<pk>/invoice/
    #   - /api/sales/orders/<pk>/deliver/
    #   - /api/sales/orders/<order_id>/history/
    #   - /api/sales/get-item-price/
    # ============================================================================

    path('exampleapi/',views.ExampleGETAPI.as_view()),

    # ============================================================================
    # Project Master — SRS Module 6
    # ============================================================================
    path('projects/', views.ProjectList.as_view()),
    path('projects/export/', views.ProjectExportView.as_view(), name='project-export'),
    path('projects/choices/', views.ProjectChoices.as_view()),
    path('projects/mini/', views.ProjectMini.as_view()),
    path('projects/<str:pk>/', views.ProjectDetail.as_view()),

]
