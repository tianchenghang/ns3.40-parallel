// Copyright 2026 hangtiancheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/*
 *  This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Faker Moatamri <faker.moatamri@sophia.inria.fr>
 */

#include "model-typeid-creator.h"

namespace ns3 {

ModelTypeidCreator::ModelTypeidCreator() {}

void

ModelTypeidCreator::Build(GtkTreeStore* treestore)
{
  m_treestore = treestore;
  m_iters.push_back(nullptr);
  Iterate();
  NS_ASSERT(m_iters.size() == 1);
}

void ModelTypeidCreator::Add(ModelTypeid *node) {
  GtkTreeIter *parent = m_iters.back();
  auto current = g_new(GtkTreeIter, 1);
  gtk_tree_store_append(m_treestore, current, parent);
  gtk_tree_store_set(m_treestore, current, COL_TYPEID, node, -1);
  m_iters.push_back(current);
}

void ModelTypeidCreator::Remove() {
  GtkTreeIter *iter = m_iters.back();
  g_free(iter);
  m_iters.pop_back();
}

void ModelTypeidCreator::VisitAttribute(TypeId tid, std::string name,
                                        std::string defaultValue,
                                        uint32_t index) {
  auto node = new ModelTypeid();
  node->type = ModelTypeid::NODE_ATTRIBUTE;
  node->tid = tid;
  node->name = name;
  node->defaultValue = defaultValue;
  node->index = index;
  Add(node);
  Remove();
}

void ModelTypeidCreator::StartVisitTypeId(std::string name) {
  auto node = new ModelTypeid();
  node->type = ModelTypeid::NODE_TYPEID;
  node->tid = TypeId::LookupByName(name);
  Add(node);
}

void ModelTypeidCreator::EndVisitTypeId() { Remove(); }
} // end namespace ns3
