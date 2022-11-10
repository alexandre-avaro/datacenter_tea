import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TEA_interface(tk.Tk):
    """
    Computes TEA for different models of data centers
    """

    def __init__(self, win):
        """
        Initiates the GUI and imports data
        """

        # Initialize TEA window
        win.title("TEA of cooling methods")
        win.iconbitmap("Stanford_icon.ico")
        win.geometry("1300x800+10+10")

        # Plotting default parameters
        plt.rcParams['font.size'] = '10'
        plt.rcParams['legend.fontsize'] = '7'
        plt.rcParams['font.sans-serif'] = 'Helvetica'
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.spines.right'] = False
        plt.rcParams['axes.spines.top'] = False

        # List of American States
        list_states = ["United States", "Alabama", "Alaska", "Arizona",
                       "Arkansas", "California", "Colorado", "Connecticut",
                       "Delaware", "Florida", "Georgia", "Hawaii",
                       "Idaho", "Illinois", "Indiana", "Iowa", "Kansas",
                       "Kentucky", "Louisiana", "Maine", "Maryland",
                       "Massachusetts", "Michigan", "Minnesota",
                       "Mississippi", "Missouri", "Montana", "Nebraska",
                       "Nevada", "New Hampshire", "New Jersey", "New Mexico",
                       "New York", "North Carolina", "North Dakota",
                       "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
                       "Rhode Island", "South Carolina", "South Dakota",
                       "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
                       "Washington", "West Virginia", "Wisconsin", "Wyoming"]

        # GUI initialization
        self.lbl1 = tk.Label(win, text='Simulation time (y)')
        self.lbl1.place(x=20, y=50)
        self.sim_time = tk.Entry()
        self.sim_time.insert(0, 20)
        self.sim_time.place(x=160, y=50)

        self.lbl2 = tk.Label(win, text='Rack consumption (kW)')
        self.lbl2.place(x=20, y=100)
        self.rack_consumption = tk.Entry()
        self.rack_consumption.insert(0, 10)
        self.rack_consumption.place(x=160, y=100)

        self.lbl3 = tk.Label(win, text='Number of racks')
        self.lbl3.place(x=310, y=50)
        self.n_racks = tk.Entry()
        self.n_racks.insert(0, 42)
        self.n_racks.place(x=410, y=50)

        self.lbl4 = tk.Label(win, text='Cases name')
        self.lbl4.place(x=310, y=100)
        self.case_name = tk.Entry()
        self.case_name.insert(0, 'Evaporative, Classic')
        self.case_name.place(x=410, y=100)

        self.lbl5 = tk.Label(win, text='PUE')
        self.lbl5.place(x=550, y=50)
        self.PUE = tk.Entry()
        self.PUE.insert(0, '1.02, 1.2')
        self.PUE.place(x=620, y=50)

        self.lbl6 = tk.Label(win, text='Lifetime (y)')
        self.lbl6.place(x=550, y=100)
        self.lifetime = tk.Entry()
        self.lifetime.insert(0, '11, 15')
        self.lifetime.place(x=620, y=100)

        self.lbl7 = tk.Label(win, text='Installation costs ($)')
        self.lbl7.place(x=750, y=50)
        self.installation_costs = tk.Entry()
        self.installation_costs.insert(0, '48700, 43200')
        self.installation_costs.place(x=860, y=50)

        self.lbl8 = tk.Label(win, text='Renewal costs ($)')
        self.lbl8.place(x=750, y=100)
        self.renewal_costs = tk.Entry()
        self.renewal_costs.insert(0, '28288, 24343')
        self.renewal_costs.place(x=860, y=100)

        self.lbl9 = tk.Label(win, text='Yearly maintenance rate (%)')
        self.lbl9.place(x=1000, y=50)
        self.maintenance_rate = tk.Entry()
        self.maintenance_rate.insert(0, '0.15, 0.19')
        self.maintenance_rate.place(x=1160, y=50)
        self.computed = False

        if not self.computed:
            self.b1 = tk.Button(win, text='Run', command=self.compute)
        else:
            self.b1 = tk.Button(win, text='Update', command=self.compute)
        self.b1.place(x=1300/2, y=140)
        self.retail_price_data = pd.read_csv(
            'Average_retail_price_of_electricity_monthly.csv', skiprows=4)

        self.activity_hours = pd.read_csv('Activity_hours_daily.csv')

        self.b2 = tk.Button(win, text='Save figure', command=self.save_results)
        self.b2.place(x=1300/2 - 80, y=140)

        self.state_name = tk.StringVar()
        self.state_name.set('California')
        self.state_menu = tk.OptionMenu(win, self.state_name, *list_states)
        self.state_menu.place(x=1300/2 + 80, y=135)

        self.secondary_plot = tk.StringVar()
        self.secondary_plot.set('None')
        list_plots = ["None", "Electricity consumption",
                      "Electricity costs", "Cooling costs",
                      "Maintenance costs", "Capital costs",
                      "Stackplot", "Stackplot without IT"]
        self.secondary_plot_menu = tk.OptionMenu(
            win, self.secondary_plot, *list_plots)
        self.secondary_plot_menu.place(x=1300/2 + 420, y=140)
        self.lb9 = tk.Label(win, text='Secondary plot')
        self.lb9.place(x=1300/2 + 330, y=145)

    def number_days(self, month):
        """
        Returns the number of days in a month
        month: 8-char string, 0-2: month code, 4-7: year
        """
        if month[:3] in ['Jan', 'Mar', 'May', 'Jul', 'Aug', 'Oct', 'Dec']:
            return 31
        elif month[:3] == 'Feb':
            if int(month[4:]) % 4 == 0:
                return 29
            else:
                return 28
        else:
            return 30

    def number_days_year(self, year):
        """
        Returns the number of days in a given year
        """
        if int(year)+2 % 4 == 0:
            return 366
        else:
            return 365

    def compute_electricity_price(self, target_state, sector='industrial'):
        """
        Computes electricity prices
        target_state: Name of the U.S. state (string)
        sector: string among 'all sectors','residential', 'commercial',
                'industrial', 'transportation', 'other'
                defaults to 'industrial'
        """

        retail_price_daily = []
        self.treated_months = []
        self.days_with_months = []

        # Clean price csv data
        for month in self.retail_price_data['Month']:
            if month not in self.treated_months:
                retail_price_daily += self.number_days(month)*[list(
                    self.retail_price_data[target_state + ' ' +
                                           sector+' cents per kilowatthour'][
                        self.retail_price_data['Month'] == month])[0]]
                self.treated_months.append(month)

        # Create month list
        for month in self.treated_months:
            for day in range(self.number_days(month)):
                self.days_with_months.append(month)

        # Keep data within sim_time_d
        self.days_with_months = np.flip(
            self.days_with_months)[-self.sim_time_d:]
        electricity_retail_price_daily = np.flip(
            retail_price_daily)[-self.sim_time_d:]/100

        return electricity_retail_price_daily

    def average_along_month(self, list_to_avg):
        treated_months = []
        avg_list = np.zeros(list_to_avg.size)
        r_in = 0
        for month in self.days_with_months:
            if month not in treated_months:
                treated_months.append(month)
                avg_list[r_in:r_in+self.number_days(month)] = [
                    np.mean(list_to_avg[r_in:r_in +
                                        self.number_days(month)])] * \
                    self.number_days(month)
                r_in += self.number_days(month)
        avg_list = np.array(avg_list).flatten()
        return avg_list

    def custom_parser(self, string, type):
        """
        Custom parser for the text inputs
        string: string to parse
        type: desired output type of the elements of the list
        """
        if ',' in string:
            str_list = string.split(',')
            l_res = []
            for el in str_list:
                if type == 'str':
                    l_res.append(el.replace(' ', ''))
                elif type == 'int':
                    l_res.append(int(el))
                elif type == 'float':
                    l_res.append(float(el))
            return l_res
        else:
            if type == 'str':
                return [string]
            elif type == 'int':
                return [int(string)]
            elif type == 'float':
                return [float(string)]

    def compute(self):
        """
        Update function
        """
        # Remove previous plots
        if self.computed:
            self.plots.get_tk_widget().destroy()
        self.computed = True

        # Get the input values
        sim_time_y = float(self.sim_time.get())
        n_rack = int(self.n_racks.get())
        rack_consumption = float(self.rack_consumption.get())
        case_name = self.custom_parser(self.case_name.get(), 'str')
        PUE = self.custom_parser(self.PUE.get(), 'float')
        lifetime_y = self.custom_parser(self.lifetime.get(), 'float')
        capital_cost_per_renewal = self.custom_parser(
            self.renewal_costs.get(), 'float')
        installation_init_cost = self.custom_parser(
            self.installation_costs.get(), 'float')
        maintenance_rate = self.custom_parser(
            self.maintenance_rate.get(), 'float')
        state_name = self.state_name.get()

        # Compute settings & initialize arrays
        self.sim_time_d = int(round(365.25*sim_time_y))
        time_days = np.linspace(1, self.sim_time_d, self.sim_time_d)
        IT_load = n_rack * rack_consumption
        n_case = len(case_name)
        activity_hours = list(self.activity_hours['hours'][-self.sim_time_d:])
        electricity_price = self.compute_electricity_price(
            target_state=state_name)

        capital_cost_d = np.zeros((n_case, time_days.size))
        elec_consumption = np.zeros((n_case, time_days.size))
        IT_cost_d = np.zeros((n_case, time_days.size))
        op_cost_d = np.zeros((n_case, time_days.size))
        total_cost_d = np.zeros((n_case, time_days.size))
        cooling_cost_evap_d = np.zeros((n_case, time_days.size))
        maintenance_cost_year_d = np.zeros((n_case, time_days.size))

        # Case iterations
        for case in range(n_case):
            lifetime_d = int(lifetime_y[case]*365)

            # Installation cost (first day)
            capital_cost_d[case][0] = installation_init_cost[case]

            # Time iterations
            for i, time in enumerate(time_days):
                year = self.days_with_months[i][-4:]

                # Replacement cost
                if time % lifetime_d == 0:
                    capital_cost_d[case][i] += capital_cost_per_renewal[case]

                # IT cost
                IT_cost_d[case][i] = IT_load * \
                    electricity_price[i] * activity_hours[i]

                # Cooling costs
                cooling_cost_evap_d[case][i] = (PUE[case]-1) * IT_load * \
                    electricity_price[i] * activity_hours[i]

                elec_consumption[case][i] = (
                    IT_cost_d[case][i]+cooling_cost_evap_d[case][i]) / \
                    electricity_price[i]
                # Maintenance costs
                maintenance_cost_year_d[case][i] = (
                    maintenance_rate[case] * installation_init_cost[case]) \
                    / self.number_days_year(year)

                # Total operational cost (daily)
                op_cost_d[case][i] = IT_cost_d[case][i] + \
                    cooling_cost_evap_d[case][i] + \
                    maintenance_cost_year_d[case][i]

            # Total cost (daily)
            total_cost_d[case] = capital_cost_d[case] + op_cost_d[case]

        # Plot setup
        self.figure = plt.Figure(figsize=(8.3, 4), dpi=150)
        self.figure.suptitle("Datacenter TEA for "+state_name)
        cmap = plt.get_cmap('viridis')
        cmap_2 = plt.get_cmap('hot')
        self.plots = FigureCanvasTkAgg(self.figure, root)
        self.plots.get_tk_widget().pack(side=tk.BOTTOM)

        # Cost of electricity plot
        if self.secondary_plot.get() in ["None", "Electricity consumption",
                                         "Electricity costs", "Cooling costs",
                                         "Maintenance costs", "Capital costs"]:
            ax1 = self.figure.add_subplot(121)
            ax1.plot(time_days/365, self.compute_electricity_price(state_name))
            ax1.set_xlabel('Time [years]')
            ax1.set_ylabel('Cost of electricity [$/kWh]')

            # Datacenter cost plot
            ax2 = self.figure.add_subplot(122)
            lines = []
            for case in range(n_case):
                line1 = ax2.plot(time_days/365,
                                 np.cumsum(total_cost_d[case]/1e3),
                                 label=case_name[case],
                                 color=cmap(case/(n_case-1) - 0.1))
                lines = lines + line1
            ax2.set_xlabel('Time [years]')
            ax2.set_ylabel('Cost of data center [k$]')

            # Optional secondary plot
            if self.secondary_plot.get() != "None":
                ax3 = ax2.twinx()
                ax3.spines['right'].set_visible(True)

                for case in range(n_case):
                    if self.secondary_plot.get() == "Electricity consumption":
                        line2 = ax3.plot(
                            time_days /
                            365, self.average_along_month(
                                elec_consumption[case])/1e3, '-',
                            label=case_name[case] + ' - Electricity',
                            color=cmap_2(case/(n_case) - 0.2))
                        ax3.set_ylabel(
                            'Monthly electricity consumption [MWh]',
                            rotation=-90)
                        ax3.yaxis.labelpad = 20

                    elif self.secondary_plot.get() == "Electricity costs":
                        line2 = ax3.plot(time_days/365,
                                         np.cumsum(
                                             (IT_cost_d[case] +
                                              cooling_cost_evap_d[case])
                                             / 1e3), '-.',
                                         label=case_name[case] +
                                         ' - Electricity',
                                         color=cmap_2(case/(n_case) - 0.2))
                        ax3.set_ylabel(
                            'Cost of electricity [k$]', rotation=-90)
                        ax3.yaxis.labelpad = 20

                    elif self.secondary_plot.get() == "Cooling costs":
                        line2 = ax3.plot(time_days/365,
                                         np.cumsum(
                                             cooling_cost_evap_d[case]/1e3),
                                         '-.',
                                         label=case_name[case] +
                                         ' - Cooling',
                                         color=cmap_2(case/(n_case) - 0.2))
                        ax3.set_ylabel('Cooling costs [k$]', rotation=-90)
                        ax3.yaxis.labelpad = 20

                    elif self.secondary_plot.get() == "Maintenance costs":
                        line2 = ax3.plot(time_days/365,
                                         np.cumsum(
                                             maintenance_cost_year_d[case] /
                                             1e3),
                                         '-.',
                                         label=case_name[case] +
                                         ' - Maintenance',
                                         color=cmap_2(case/(n_case) - 0.2))
                        ax3.set_ylabel('Maintenance costs [k$]', rotation=-90)
                        ax3.yaxis.labelpad = 20

                    elif self.secondary_plot.get() == "Capital costs":
                        line2 = ax3.plot(time_days/365,
                                         np.cumsum(
                                             capital_cost_d[case]/1e3),
                                         '-.',
                                         label=case_name[case] +
                                         ' - Capex',
                                         color=cmap_2(case/(n_case) - 0.2))
                        ax3.set_ylabel('Capital costs [k$]', rotation=-90)
                        ax3.yaxis.labelpad = 20
                    lines = lines + line2

            if self.secondary_plot.get() == "Electricity consumption":
                ax2.legend(handles=lines, loc='center left')
            else:
                ax2.legend(handles=lines, loc='best')

        elif self.secondary_plot.get() == "Stackplot":
            ax1 = self.figure.add_subplot(121)
            ax2 = self.figure.add_subplot(122)
            ax1.set_xlabel('Time [years]')
            ax1.set_ylabel('Cost decomposition of ' +
                           str(case_name[0])+' [k$]')
            ax2.set_xlabel('Time [years]')
            ax2.set_ylabel('Cost decomposition of ' +
                           str(case_name[1])+' [k$]',
                           rotation=-90)

            stack0 = np.vstack([np.cumsum(
                IT_cost_d[0]/1e3), np.cumsum(
                    cooling_cost_evap_d[0])
                / 1e3, np.cumsum(
                maintenance_cost_year_d[0]/1e3), np.cumsum(
                capital_cost_d[0]/1e3)])
            stack1 = np.vstack([np.cumsum(
                IT_cost_d[1]/1e3), np.cumsum(
                    cooling_cost_evap_d[1])
                / 1e3, np.cumsum(
                maintenance_cost_year_d[1]/1e3), np.cumsum(
                capital_cost_d[1]/1e3)])

            labels = ['IT', 'Cooling', 'Maintenance',
                      'Capital costs']

            line1 = ax1.stackplot(time_days/365,
                                  stack0, colors=[cmap(1/5), cmap(2/5),
                                                  cmap(3/5), cmap(4/5)],
                                  labels=labels)
            line2 = ax2.stackplot(time_days/365,
                                  stack1, colors=[cmap(1/5), cmap(2/5),
                                                  cmap(3/5), cmap(4/5)],
                                  labels=labels)

            ax1.legend(loc='upper left')
            ax1.set_ylim([0, 1e-3*np.max([np.max(np.cumsum(total_cost_d[0])),
                                          np.max(np.cumsum(total_cost_d[1]))])
                          ])
            ax2.set_ylim([0, 1e-3 * np.max([np.max(np.cumsum(total_cost_d[0])),
                                            np.max(np.cumsum(total_cost_d[1]))]
                                           )
                          ])
            ax2.yaxis.set_label_position("right")
            ax2.spines['left'].set_visible(False)
            ax2.spines['right'].set_visible(True)
            ax2.yaxis.labelpad = 10
            ax2.yaxis.tick_right()

        elif self.secondary_plot.get() == "Stackplot without IT":
            ax1 = self.figure.add_subplot(121)
            ax2 = self.figure.add_subplot(122)
            ax1.set_xlabel('Time [years]')
            ax1.set_ylabel('Cost decomposition of ' +
                           str(case_name[0])+' [k$]')
            ax2.set_xlabel('Time [years]')
            ax2.set_ylabel('Cost decomposition of ' +
                           str(case_name[1])+' [k$]',
                           rotation=-90)

            stack0 = np.vstack([np.cumsum(
                cooling_cost_evap_d[0])
                / 1e3, np.cumsum(
                maintenance_cost_year_d[0]/1e3), np.cumsum(
                capital_cost_d[0]/1e3)])
            stack1 = np.vstack([np.cumsum(
                cooling_cost_evap_d[1])
                / 1e3, np.cumsum(
                maintenance_cost_year_d[1]/1e3), np.cumsum(
                capital_cost_d[1]/1e3)])

            labels = ['Cooling', 'Maintenance',
                      'Capital costs']

            line1 = ax1.stackplot(time_days/365,
                                  stack0, colors=[cmap(2/5),
                                                  cmap(3/5), cmap(4/5)],
                                  labels=labels)
            line2 = ax2.stackplot(time_days/365,
                                  stack1, colors=[cmap(2/5),
                                                  cmap(3/5), cmap(4/5)],
                                  labels=labels)

            ax1.legend(loc='upper left')
            max_y = 1e-3*np.max([np.max(np.cumsum(total_cost_d[0]-IT_cost_d[0]
                                                  )),
                                 np.max(np.cumsum(total_cost_d[1]-IT_cost_d[1]
                                                  ))])
            ax1.set_ylim([0, max_y])
            ax2.set_ylim([0, max_y])
            ax2.yaxis.set_label_position("right")
            ax2.spines['left'].set_visible(False)
            ax2.spines['right'].set_visible(True)
            ax2.yaxis.labelpad = 15
            ax2.yaxis.tick_right()

    def save_results(self):
        """
        Saves current figure as png file in the current directory
        """
        if self.computed:
            self.figure.savefig('./tea_for_' +
                                self.state_name.get()+'.png', dpi=300)
        else:
            print("No figure to save.")


if __name__ == "__main__":
    root = tk.Tk()
    TEA_interface(root)
    root.mainloop()
