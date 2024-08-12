Here's how you can set up a Docker container running MongoDB with passthrough to a local directory, following a similar approach to the one you used for TimeScaleDB:

## Docker Container with MongoDB & Passthrough

Running MongoDB in a Docker container with passthrough to a local directory is a great way to manage your databases locally without running into storage limitations. This setup is particularly useful for development purposes, allowing you to keep your data persistent outside the container.

### Steps to Set Up MongoDB in Docker with Passthrough:

1. **Check Running Containers**: Before starting, make sure there are no conflicting containers by running the command:
   ```bash
   docker ps
   ```

2. **Pull the MongoDB Image**: Get the latest MongoDB Docker image:
   ```bash
   docker pull mongo
   ```

3. **Initialize Volumes**: Create a new Docker container for MongoDB and use a host directory as a data volume. This approach helps you bypass the container's default volume size limits by storing data directly on your local disk.

   ```bash
    cd C:/Users/shavh/Documents
   # Create a directory for MongoDB data
   rm -rf mongodb_data && mkdir mongodb_data && cd mongodb_data

   # Run the MongoDB container with a passthrough to the local directory
   docker run -d --name mongodb -p 27017:27017 -v /"$(pwd)":/data/db mongo
   ```

   > **Note:** Similar to the TimeScaleDB setup, if you're using Git Bash on Windows, you might need to escape the path conversion by prefixing it with `/${PWD}:/data/db`.

4. **Access MongoDB Environment**: Enter the MongoDB container using an interactive `bash` shell:

   ```bash
   winpty docker exec -it mongodb bash
   ```

5. **Connect to MongoDB**: Once inside the container, use the MongoDB shell (`mongo`) to interact with the database:

   ```bash
   mongo
   ```

6. **Create a New Database**: In the MongoDB shell, you can create a new database by simply switching to it:

   ```bash
   use mydatabase
   ```

   MongoDB creates the database once you insert data into it.

7. **Insert Data**: You can insert a document into a collection to create the collection and the database:

   ```bash
   db.mycollection.insert({ name: "example", type: "test" })
   ```

8. **Check Data**: Verify the data by querying the collection:

   ```bash
   db.mycollection.find()
   ```

9. **Confirm Volume Binding**: To ensure the passthrough mount is working correctly, exit the MongoDB shell and inspect the Docker container:

   ```bash
   docker inspect mongodb
   ```

   Look for the volume bindings in the output to confirm that your local directory is correctly mapped to the container's `/data/db`.

### Summary

With these steps, you'll have MongoDB running in a Docker container with a passthrough mount to your local disk. This setup ensures that your data persists outside the container, even if the container is removed or stopped. It's a reliable and efficient way to handle local MongoDB instances, especially for development purposes.