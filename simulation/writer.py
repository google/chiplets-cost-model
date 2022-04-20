import csv

def create_row(category, option1, option2, numOfYr):
    row = {'CostCategory': category}

    for year in range(1, numOfYr + 1):
        col_name = f'ChipletYr{year}'
        row[col_name] = option1[year - 1]

    for year in range(1, numOfYr + 1):
        col_name = f'2SocChipsYr{year}'
        row[col_name] = option2[year - 1]

    return row


def write_to_file(summary, years):
    with open('outputs/summary_output.csv', 'w') as file:

        field_names = ['CostCategory']
        
        for year in range(1, years + 1):
            col_name = f'ChipletYr{year}'
            field_names.append(col_name)

        for year in range(1, years + 1):
            col_name = f'2SocChipsYr{year}'
            field_names.append(col_name)
        
        writer = csv.DictWriter(file, field_names)
        writer.writeheader()
        writer.writerows(summary)
