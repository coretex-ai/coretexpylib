#!/bin/bash

# Prompt the user for input
read -p "Enter username: " username
read -sp "Enter password: " password
echo
read -p "Enter machine name (queue name): " machine_name

# Encode the username and password in base64
encoded_username=$(echo -n "$username" | base64)
encoded_password=$(echo -n "$password" | base64)

# Path to the template and output file
template_path="./node_deployment_template.yaml"
output_path="./node_deployment.yaml"

# Replace the placeholders with the user's input
sed "s/\${INSERT_USERNAME_HERE}/$encoded_username/g; s/\${INSERT_PASSWORD_HERE}/$encoded_password/g; s/\${INSERT_QUEUE_NAME_HERE}/$machine_name/g" "$template_path" > "$output_path"

echo "The file has been created at $output_path"
