function update_tables(){
		$.getJSON(
			'http://127.0.0.1:8080/statistics',
			function proc(data){
				var table;
    			for(table_name in data){
    				console.log('Updating table: ' + table_name);
    				table = $("#" + table_name.replace(/ /gi, "_")).DataTable();
    	    		table.clear();
    				for(i in data[table_name]['data']){
    					r = data[table_name]['data'][i]
    					var row = [];
    					for(j in data[table_name]['headers']){
    						key = data[table_name]['headers'][j]
        					row.push(r[key])
    					};
	    				table.row.add(row);
    				};
    				table.draw();
    			};
			}
		);
	};
update_tables();
setInterval(update_tables, 30000);
