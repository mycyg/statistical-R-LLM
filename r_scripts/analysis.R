# analysis.R

# Get command line arguments
args <- commandArgs(trailingOnly = TRUE)

# Check if the correct number of arguments is provided
if (length(args) != 1) {
  stop("Usage: Rscript analysis.R <input_csv_path>", call. = FALSE)
}

# Get the input file path
input_file <- args[1]

# Read the data
data <- read.csv(input_file)

# Perform a summary
summary_output <- summary(data)

# Print the summary to standard output
print(summary_output)
