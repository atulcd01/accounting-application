
Vue.component('accounts', {
  template: `
    <div>
	  <table id="example" class="table  table-bordered  " style="width:100%"> </table>
	 </div>
  `,
  data() {
axios
				  .get('http://127.0.0.1:5000/accounts')
   			  	.then(response => {
						var dataSet = response.data.accounts
						var table = $('#example').DataTable( {
							data: dataSet,
							columns: [
								{ title: "Code" },
								{ title: "Name" },
								{ title: "Phone" },
								{ title: "Email" },
								{ title: "Balance" }
							], 
							"lengthMenu": [[50, 100, -1], [50, 100, "All"]]
						} );


	 $('#example tbody').on('dblclick', 'tr', function () {
        var data = table.row( this ).data();
		account_code = data[0]
		account_name  = data[1]
	    vm.ledger(account_code, account_name)
    } );
		})
    return { checked: false, title: 'Check me' }
  },
  methods: {
 
  }
});



