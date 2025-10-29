-- Create project table
CREATE TABLE `project` (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(255),
    `sum` INT,
    `charts` INT NOT NULL,
    `pinned_opened` INT NOT NULL,
    `hidden_opened` INT NOT NULL,
    `more` VARCHAR(255),
    `version` VARCHAR(30) NOT NULL,
    `create_time` VARCHAR(30) NOT NULL,
    `update_time` VARCHAR(30) NOT NULL
);

-- Create unique index on project name
CREATE UNIQUE INDEX `project_name` ON `project` (`name`);

-- Create experiment table
CREATE TABLE `experiment` (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `run_id` VARCHAR(255) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(255),
    `sort` INT NOT NULL,
    `status` INT NOT NULL,
    `show` INT NOT NULL,
    `light` VARCHAR(20),
    `dark` VARCHAR(20),
    `pinned_opened` INT NOT NULL,
    `hidden_opened` INT NOT NULL,
    `more` TEXT,
    `version` VARCHAR(30) NOT NULL,
    `create_time` VARCHAR(30) NOT NULL,
    `finish_time` VARCHAR(30),
    `update_time` VARCHAR(30) NOT NULL,
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (`sort` >= 0)
);

-- Create indexes for experiment table
CREATE INDEX `experiment_project_id` ON `experiment` (`project_id`);
CREATE UNIQUE INDEX `experiment_run_id` ON `experiment` (`run_id`);
CREATE UNIQUE INDEX `experiment_name_project_id` ON `experiment` (`name`, `project_id`);
CREATE UNIQUE INDEX `experiment_sort_project_id` ON `experiment` (`sort`, `project_id`);

-- Create chart table
CREATE TABLE `chart` (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `experiment_id` INT,
    `project_id` INT,
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(255),
    `system` INT NOT NULL,
    `type` VARCHAR(10) NOT NULL,
    `reference` VARCHAR(10) NOT NULL,
    `status` INT NOT NULL,
    `sort` INT,
    `config` TEXT,
    `more` TEXT,
    `create_time` VARCHAR(30) NOT NULL,
    `update_time` VARCHAR(30) NOT NULL,
    FOREIGN KEY (`experiment_id`) REFERENCES `experiment` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create indexes for chart table
CREATE INDEX `chart_experiment_id` ON `chart` (`experiment_id`);
CREATE INDEX `chart_project_id` ON `chart` (`project_id`);
CREATE UNIQUE INDEX `chart_name_experiment_id` ON `chart` (`name`, `experiment_id`);
CREATE UNIQUE INDEX `chart_name_project_id` ON `chart` (`name`, `project_id`);

-- Create namespace table
CREATE TABLE `namespace` (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `experiment_id` INT,
    `project_id` INT,
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(255),
    `sort` INT NOT NULL,
    `opened` INT NOT NULL,
    `more` TEXT,
    `create_time` VARCHAR(30) NOT NULL,
    `update_time` VARCHAR(30) NOT NULL,
    FOREIGN KEY (`experiment_id`) REFERENCES `experiment` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (`sort` >= 0)
);

-- Create indexes for namespace table
CREATE INDEX `namespace_experiment_id` ON `namespace` (`experiment_id`);
CREATE INDEX `namespace_project_id` ON `namespace` (`project_id`);
CREATE UNIQUE INDEX `namespace_name_experiment_id` ON `namespace` (`name`, `experiment_id`);
CREATE UNIQUE INDEX `namespace_name_project_id` ON `namespace` (`name`, `project_id`);

-- Create display table
CREATE TABLE `display` (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `chart_id` INT NOT NULL,
    `namespace_id` INT NOT NULL,
    `sort` INT NOT NULL,
    `more` TEXT,
    `create_time` VARCHAR(30) NOT NULL,
    `update_time` VARCHAR(30) NOT NULL,
    FOREIGN KEY (`chart_id`) REFERENCES `chart` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`namespace_id`) REFERENCES `namespace` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (`sort` >= 0)
);

-- Create indexes for display table
CREATE INDEX `display_chart_id` ON `display` (`chart_id`);
CREATE INDEX `display_namespace_id` ON `display` (`namespace_id`);
CREATE UNIQUE INDEX `display_chart_id_namespace_id` ON `display` (`chart_id`, `namespace_id`);

-- Create tag table
CREATE TABLE `tag` (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `experiment_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `folder` VARCHAR(255),
    `type` VARCHAR(10) NOT NULL,
    `description` VARCHAR(100),
    `system` INT NOT NULL,
    `sort` INT NOT NULL,
    `more` TEXT,
    `create_time` VARCHAR(30) NOT NULL,
    `update_time` VARCHAR(30) NOT NULL,
    FOREIGN KEY (`experiment_id`) REFERENCES `experiment` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create indexes for tag table
CREATE INDEX `tag_experiment_id` ON `tag` (`experiment_id`);
CREATE UNIQUE INDEX `tag_name_experiment_id` ON `tag` (`name`, `experiment_id`);

-- Create source table
CREATE TABLE `source` (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `tag_id` INT NOT NULL,
    `chart_id` INT NOT NULL,
    `sort` INT NOT NULL,
    `error` TEXT,
    `more` TEXT,
    `create_time` VARCHAR(30) NOT NULL,
    `update_time` VARCHAR(30) NOT NULL,
    FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`chart_id`) REFERENCES `chart` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create indexes for source table
CREATE INDEX `source_tag_id` ON `source` (`tag_id`);
CREATE INDEX `source_chart_id` ON `source` (`chart_id`);
CREATE UNIQUE INDEX `source_tag_id_chart_id` ON `source` (`tag_id`, `chart_id`);