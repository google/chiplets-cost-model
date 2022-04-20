import csv

def write_to_file(summary, numOfYears):
    with open('outputs/summary_output.csv', 'w') as file:

        field_names = ['CostCategory']
        
        for year in range(1, numOfYears + 1):
            col_name = f'ChipletYr{year}'
            field_names.append(col_name)

        for year in range(1, numOfYears + 1):
            col_name = f'2SocChipsYr{year}'
            field_names.append(col_name)
        
        writer = csv.DictWriter(file, field_names)
        writer.writeheader()
        writer.writerows(summary)
