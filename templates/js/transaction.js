
Vue.component('transaction', {
  template: `
    <div>
	  <table id="example" class="table  table-bordered  " style="width:100%"> </table>
	 </div>
  `,
  data() {
					axios
					.get('http://127.0.0.1:5000/transactions')
					.then(response => {
							var dataSet = response.data.transactions
							var table = $('#example').DataTable( {
								data: dataSet,
								columns: [
									{ title: "Date" },
									{ title: "Name" },
									{ title: "Credit Account" },
									{ title: "Debit Account" },
									{ title: "Balance" }
								], 
								"lengthMenu": [[50, 100, -1], [50, 100, "All"]]
							} );
		})
    return { checked: false, title: 'Check me' }
  },
  methods: {
 
  }
});



